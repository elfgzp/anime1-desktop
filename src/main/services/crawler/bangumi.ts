/**
 * Bangumi 爬虫
 * 
 * 对应原项目: src/parser/cover_finder.py
 */

import * as cheerio from 'cheerio'
import log from 'electron-log'
import type { BangumiInfo, BangumiSearchResult } from '@shared/types'
import { URLS, BANGUMI_CONFIG, PATTERNS } from '@shared/constants'
import { HttpClient, createDefaultHttpClient } from './http-client'

export class BangumiCrawler {
  private httpClient: HttpClient

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createDefaultHttpClient()
  }

  /**
   * 搜索 Bangumi
   * 对应: src/parser/cover_finder.py - search_bangumi
   */
  async searchByTitle(title: string): Promise<BangumiSearchResult[]> {
    log.info(`[Bangumi] Searching: ${title}`)
    
    try {
      // 使用 Bangumi API
      const encodedTitle = encodeURIComponent(title)
      const searchUrl = `${URLS.BANGUMI_API}/search/subject/${encodedTitle}?type=2&responseGroup=small&max_results=${BANGUMI_CONFIG.RESULT_LIMIT}`
      
      const data = await this.httpClient.get<any>(searchUrl)
      
      if (!data.list || !Array.isArray(data.list)) {
        return []
      }
      
      return data.list.map((item: any) => ({
        id: item.id,
        title: item.name,
        titleCn: item.name_cn,
        coverUrl: item.images?.common,
        type: item.type,
        score: item.rating?.score,
        rank: item.rank,
        date: item.air_date
      }))
    } catch (error) {
      log.warn('[Bangumi] API search failed, falling back to HTML:', error)
      return this.searchByHtml(title)
    }
  }

  /**
   * 通过 HTML 页面搜索（备用方法）
   */
  private async searchByHtml(title: string): Promise<BangumiSearchResult[]> {
    try {
      const encodedTitle = encodeURIComponent(title)
      const searchUrl = `${URLS.BANGUMI_BASE}/subject_search/${encodedTitle}?cat=2`
      
      const html = await this.httpClient.get<string>(searchUrl)
      const $ = cheerio.load(html)
      
      const results: BangumiSearchResult[] = []
      
      $('#browserItemList li.item').each((_, elem) => {
        const $elem = $(elem)
        
        const $link = $elem.find('a.subjectCover')
        const href = $link.attr('href') || ''
        const idMatch = href.match(/\/subject\/(\d+)/)
        if (!idMatch) return
        
        const id = parseInt(idMatch[1], 10)
        const title = $elem.find('.subjectTitle a').text().trim()
        const titleCn = $elem.find('.subjectTitle .tip').text().trim()
        const coverUrl = $link.find('img').attr('src')
        const scoreText = $elem.find('.rateInfo .smallStars').parent().text().trim()
        const score = scoreText ? parseFloat(scoreText) : undefined
        
        results.push({
          id,
          title,
          titleCn: titleCn || undefined,
          coverUrl: coverUrl ? `https:${coverUrl}` : undefined,
          score
        })
      })
      
      return results.slice(0, BANGUMI_CONFIG.RESULT_LIMIT)
    } catch (error) {
      log.error('[Bangumi] HTML search failed:', error)
      return []
    }
  }

  /**
   * 获取 Bangumi 详细信息
   */
  async getSubjectInfo(subjectId: number): Promise<BangumiInfo | null> {
    log.info(`[Bangumi] Getting subject info: ${subjectId}`)
    
    try {
      const url = `${URLS.BANGUMI_API}/subject/${subjectId}?responseGroup=large`
      const data = await this.httpClient.get<any>(url)
      
      if (!data || data.type !== 2) { // type 2 = anime
        return null
      }
      
      const info: BangumiInfo = {
        title: data.name_cn || data.name,
        subjectUrl: `${URLS.BANGUMI_BASE}/subject/${subjectId}`,
        coverUrl: data.images?.common ? `https:${data.images.common}` : undefined,
        rating: data.rating?.score,
        rank: data.rank,
        type: this.mapType(data.type),
        date: data.air_date,
        summary: data.summary,
        genres: data.tags?.map((t: any) => t.name) || [],
        staff: [],
        cast: []
      }
      
      // 提取 staff
      if (data.staff) {
        info.staff = data.staff.map((s: any) => ({
          name: s.name,
          role: s.jobs?.join(', ') || 'Staff'
        }))
      }
      
      // 提取 cast
      if (data.crt) {
        info.cast = data.crt
          .filter((c: any) => c.actors && c.actors.length > 0)
          .slice(0, 10)
          .map((c: any) => ({
            name: c.actors[0].name,
            character: c.name
          }))
      }
      
      return info
    } catch (error) {
      log.error('[Bangumi] Failed to get subject info:', error)
      return null
    }
  }

  /**
   * 查找最佳匹配的 Bangumi 信息
   * 对应: src/parser/cover_finder.py - get_bangumi_info
   */
  async findBestMatch(
    title: string,
    year?: string,
    season?: string
  ): Promise<{ info: BangumiInfo; score: number } | null> {
    log.info(`[Bangumi] Finding best match for: ${title}`)
    
    // 搜索
    const searchResults = await this.searchByTitle(title)
    if (searchResults.length === 0) {
      log.info('[Bangumi] No search results')
      return null
    }
    
    // 计算匹配分数
    let bestMatch: { result: BangumiSearchResult; score: number } | null = null
    
    for (const result of searchResults) {
      const score = this.calculateMatchScore(title, result, year, season)
      
      if (!bestMatch || score > bestMatch.score) {
        bestMatch = { result, score }
      }
    }
    
    if (!bestMatch || bestMatch.score < BANGUMI_CONFIG.MIN_MATCH_SCORE) {
      log.info(`[Bangumi] No good match found (best score: ${bestMatch?.score ?? 0})`)
      return null
    }
    
    log.info(`[Bangumi] Best match: ${bestMatch.result.title} (score: ${bestMatch.score})`)
    
    // 获取详细信息
    const info = await this.getSubjectInfo(bestMatch.result.id)
    if (!info) {
      return null
    }
    
    return { info, score: bestMatch.score }
  }

  /**
   * 计算匹配分数
   * 对应: src/parser/cover_finder.py - 各种匹配算法
   */
  private calculateMatchScore(
    queryTitle: string,
    result: BangumiSearchResult,
    year?: string,
    season?: string
  ): number {
    const titles = [result.title, result.titleCn].filter(Boolean) as string[]
    let maxScore = 0
    
    for (const title of titles) {
      const score = this.matchTitles(queryTitle, title)
      maxScore = Math.max(maxScore, score)
    }
    
    // 年份匹配加分
    if (year && result.date) {
      const resultYear = result.date.substring(0, 4)
      if (resultYear === year) {
        maxScore += 10
      }
    }
    
    return Math.min(maxScore, 100)
  }

  /**
   * 标题匹配算法
   */
  private matchTitles(query: string, target: string): number {
    const q = query.toLowerCase().trim()
    const t = target.toLowerCase().trim()
    
    // 完全匹配
    if (q === t) return 100
    
    // 包含匹配
    if (t.includes(q)) return 90
    if (q.includes(t)) return 85
    
    // 清理后的匹配
    const cleanQ = this.cleanTitle(q)
    const cleanT = this.cleanTitle(t)
    
    if (cleanQ === cleanT) return 80
    if (cleanT.includes(cleanQ)) return 70
    if (cleanQ.includes(cleanT)) return 65
    
    // 中文关键词匹配
    const qKeywords = this.extractChineseKeywords(q)
    const tKeywords = this.extractChineseKeywords(t)
    
    if (qKeywords.length > 0 && tKeywords.length > 0) {
      const common = qKeywords.filter(k => tKeywords.includes(k))
      const overlap = common.length / Math.max(qKeywords.length, tKeywords.length)
      return Math.floor(overlap * 50)
    }
    
    return 0
  }

  /**
   * 清理标题
   */
  private cleanTitle(title: string): string {
    return title
      .replace(PATTERNS.CLEAN_TITLE, '')
      .replace(/\s+/g, ' ')
      .trim()
  }

  /**
   * 提取中文关键词
   */
  private extractChineseKeywords(title: string): string[] {
    const chineseChars = title.match(/[\u4e00-\u9fa5]+/g) || []
    return chineseChars.filter(c => c.length >= 2)
  }

  /**
   * 映射类型
   */
  private mapType(type: number): string {
    const typeMap: Record<number, string> = {
      1: 'book',
      2: 'anime',
      3: 'music',
      4: 'game',
      6: 'real'
    }
    return typeMap[type] || 'unknown'
  }

  /**
   * 关闭爬虫
   */
  close(): void {
    this.httpClient.close()
    log.info('[Bangumi] Crawler closed')
  }
}
