/**
 * Bangumi 爬虫
 * 
 * 对应原项目: src/parser/cover_finder.py
 * 核心改进:
 * - 支持简繁体转换搜索
 * - 核心关键词提取
 * - 完善的匹配评分算法（年份、排名、评分）
 * - 封面URL自动修复
 */

import * as cheerio from 'cheerio'
import log from 'electron-log'
import * as OpenCC from 'opencc-js'
import type { BangumiInfo, BangumiSearchResult } from '@shared/types'
import { URLS, BANGUMI_CONFIG } from '@shared/constants'
import { HttpClient, createDefaultHttpClient } from './http-client'

// 匹配配置（与Python版本保持一致）
const MATCH_CONFIG = {
  MIN_MATCH_SCORE: 30,     // Python版本是30，不是60
  YEAR_MATCH_BONUS: 15,
  YEAR_MISMATCH_PENALTY: 10,
  RANK_TOP100_BONUS: 10,
  RANK_TOP500_BONUS: 5,
  RANK_TOP1000_BONUS: 3,
  RATING_HIGH_BONUS: 5,    // >= 8.0
  RATING_GOOD_BONUS: 3,    // >= 7.0
}

export class BangumiCrawler {
  private httpClient: HttpClient
  private t2sConverter: any // 繁体转简体
  private s2tConverter: any // 简体转繁体

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createDefaultHttpClient()
    // 初始化转换器
    try {
      this.t2sConverter = OpenCC.Converter({ from: 'tw', to: 'cn' })
      this.s2tConverter = OpenCC.Converter({ from: 'cn', to: 'tw' })
    } catch (e) {
      log.warn('[Bangumi] OpenCC init failed:', e)
    }
  }

  /**
   * 繁体转简体
   */
  private toSimplified(text: string): string {
    if (!this.t2sConverter) return text
    try {
      return this.t2sConverter(text)
    } catch (e) {
      return text
    }
  }

  /**
   * 简体转繁体
   */
  private toTraditional(text: string): string {
    if (!this.s2tConverter) return text
    try {
      return this.s2tConverter(text)
    } catch (e) {
      return text
    }
  }

  /**
   * 获取标题的各种变体（简体、繁体）
   * 对应: _get_title_variants
   */
  private getTitleVariants(title: string): string[] {
    const variants = new Set<string>([title])
    
    // 添加繁体版本
    const traditional = this.toTraditional(title)
    if (traditional !== title) {
      variants.add(traditional)
    }
    
    // 添加简体版本
    const simplified = this.toSimplified(title)
    if (simplified !== title) {
      variants.add(simplified)
    }
    
    return Array.from(variants)
  }

  /**
   * 提取核心关键词
   * 对应: _extract_core_keyword
   * 例如: "鬼灭之刃 第二季" -> "鬼灭之刃"
   */
  private extractCoreKeyword(title: string): string {
    let result = title
    
    // 移除季数信息
    const patterns = [
      /\s*第[一二三四五六七八九十\d]+季/g,
      /\s*Season\s*\d+/gi,
      /\s*\d+期/g,
      /\s*\(\d{4}\)/g,
    ]
    
    for (const pattern of patterns) {
      result = result.replace(pattern, '')
    }
    
    // 移除冒号后的副标题
    if (result.includes(':')) {
      result = result.split(':')[0]
    }
    if (result.includes('：')) {
      result = result.split('：')[0]
    }
    
    return result.trim()
  }

  /**
   * 标准化标题用于比较
   * 对应: _normalize_title
   */
  private normalizeTitle(title: string): string {
    // 转小写
    title = title.toLowerCase()
    // 移除特殊字符，保留中文和英文单词字符
    title = title.replace(/[^\w\u4e00-\u9fa5]/g, '')
    return title
  }

  /**
   * 搜索 Bangumi
   * 支持简体/繁体双重搜索
   * 对应: search_bangumi
   */
  async searchByTitle(title: string): Promise<BangumiSearchResult[]> {
    log.info(`[Bangumi] Searching: ${title}`)
    
    const searchTerms = this.getTitleVariants(title)
    const allResults: BangumiSearchResult[] = []
    const seenIds = new Set<number>()
    
    // 搜索所有变体
    for (const term of searchTerms) {
      if (!term.trim()) continue
      
      try {
        const results = await this.searchByApi(term)
        // 合并结果（去重）
        for (const result of results) {
          if (!seenIds.has(result.id)) {
            seenIds.add(result.id)
            allResults.push(result)
          }
        }
      } catch (error) {
        log.warn(`[Bangumi] Search failed for "${term}":`, error)
      }
    }
    
    return allResults
  }

  /**
   * 使用 API 搜索
   */
  private async searchByApi(title: string): Promise<BangumiSearchResult[]> {
    try {
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
   * 计算匹配分数
   * 对应: _calculate_match_score
   * 关键改进: 匹配时也考虑简繁体变体
   */
  private calculateMatchScore(
    queryTitle: string,
    result: BangumiSearchResult,
    year?: string
  ): number {
    let score = 0
    
    // 获取查询标题的所有变体（简体、繁体）
    const queryVariants = this.getTitleVariants(queryTitle)
    
    // 获取结果的所有标题
    const resultTitles = [result.title, result.titleCn].filter(Boolean) as string[]
    
    // 计算最佳匹配分数（考虑所有查询变体）
    let bestTitleScore = 0
    
    for (const queryVariant of queryVariants) {
      const queryNormalized = this.normalizeTitle(queryVariant)
      
      for (const resultTitle of resultTitles) {
        if (!resultTitle) continue
        
        const resultNormalized = this.normalizeTitle(resultTitle)
        
        // 完全匹配
        if (queryNormalized === resultNormalized) {
          bestTitleScore = 100
          break
        }
        
        // 包含匹配
        if (queryNormalized.includes(resultNormalized) || resultNormalized.includes(queryNormalized)) {
          bestTitleScore = Math.max(bestTitleScore, 80)
        }
        
        // 字符级别相似度
        const queryChars = new Set(queryNormalized)
        const resultChars = new Set(resultNormalized)
        if (queryChars.size > 0 && resultChars.size > 0) {
          const common = new Set([...queryChars].filter(c => resultChars.has(c)))
          const similarity = common.size / Math.max(queryChars.size, resultChars.size)
          const keywordScore = similarity * 60
          bestTitleScore = Math.max(bestTitleScore, keywordScore)
        }
      }
      
      // 如果已经满分，提前退出
      if (bestTitleScore === 100) break
    }
    
    score += bestTitleScore
    
    // 年份匹配
    if (year && result.date) {
      const resultYear = result.date.substring(0, 4)
      if (resultYear === year) {
        score += MATCH_CONFIG.YEAR_MATCH_BONUS
      } else if (Math.abs(parseInt(resultYear) - parseInt(year)) <= 1) {
        score += MATCH_CONFIG.YEAR_MATCH_BONUS / 2
      } else {
        score -= MATCH_CONFIG.YEAR_MISMATCH_PENALTY
      }
    }
    
    // Bangumi排名加分
    const rank = result.rank
    if (rank && typeof rank === 'number' && rank > 0) {
      if (rank <= 100) {
        score += MATCH_CONFIG.RANK_TOP100_BONUS
      } else if (rank <= 500) {
        score += MATCH_CONFIG.RANK_TOP500_BONUS
      } else if (rank <= 1000) {
        score += MATCH_CONFIG.RANK_TOP1000_BONUS
      }
    }
    
    // 评分加分
    const rating = result.score
    if (rating && typeof rating === 'number') {
      if (rating >= 8) {
        score += MATCH_CONFIG.RATING_HIGH_BONUS
      } else if (rating >= 7) {
        score += MATCH_CONFIG.RATING_GOOD_BONUS
      }
    }
    
    return Math.min(score, 100)
  }

  /**
   * 检查是否已经有好的匹配
   */
  private hasGoodMatch(
    results: BangumiSearchResult[],
    title: string,
    year?: string
  ): boolean {
    for (const result of results) {
      const score = this.calculateMatchScore(title, result, year)
      if (score >= MATCH_CONFIG.MIN_MATCH_SCORE) {
        return true
      }
    }
    return false
  }

  /**
   * 查找最佳匹配的 Bangumi 信息
   * 对应: find_cover
   */
  async findBestMatch(
    title: string,
    year?: string,
    season?: string
  ): Promise<{ info: BangumiInfo; score: number } | null> {
    log.info(`[Bangumi] Finding best match for: ${title}, year=${year}, season=${season}`)
    
    // 1. 首先用完整标题搜索
    let searchResults = await this.searchByTitle(title)
    
    // 2. 如果没有好的匹配，尝试核心关键词搜索
    if (searchResults.length === 0 || !this.hasGoodMatch(searchResults, title, year)) {
      const coreKeyword = this.extractCoreKeyword(title)
      if (coreKeyword && coreKeyword !== title && coreKeyword.length >= 2) {
        log.info(`[Bangumi] Trying core keyword: ${coreKeyword}`)
        const keywordResults = await this.searchByTitle(coreKeyword)
        // 合并结果（去重）
        const seenIds = new Set(searchResults.map(r => r.id))
        for (const result of keywordResults) {
          if (!seenIds.has(result.id)) {
            searchResults.push(result)
          }
        }
      }
    }
    
    if (searchResults.length === 0) {
      log.info('[Bangumi] No search results')
      
      // 3. 尝试 Wikipedia fallback
      const wikiResult = await this.searchWikipedia(title)
      if (wikiResult) {
        return { info: wikiResult, score: 0 }
      }
      
      return null
    }
    
    // 4. 计算匹配分数并排序
    const scoredResults = searchResults.map(result => ({
      result,
      score: this.calculateMatchScore(title, result, year)
    }))
    
    scoredResults.sort((a, b) => b.score - a.score)
    
    // 5. 选择最佳匹配
    const bestMatch = scoredResults[0]
    log.info(`[Bangumi] Best match: ${bestMatch.result.title} (score: ${bestMatch.score.toFixed(1)})`)
    
    // 6. 获取详细信息
    const info = await this.getSubjectInfo(bestMatch.result.id)
    if (!info) {
      return null
    }
    
    // 如果没有达到分数阈值，仍然返回但标记为低置信度（与Python版本一致）
    if (bestMatch.score < MATCH_CONFIG.MIN_MATCH_SCORE) {
      log.info(`[Bangumi] Low confidence match (score: ${bestMatch.score.toFixed(1)} < ${MATCH_CONFIG.MIN_MATCH_SCORE})`)
      return { info, score: 0 }
    }
    
    return { info, score: bestMatch.score }
  }

  /**
   * 搜索 Wikipedia 作为 fallback
   * 对应: _search_wikipedia
   */
  private async searchWikipedia(title: string): Promise<BangumiInfo | null> {
    log.info(`[Wikipedia] Searching fallback for: ${title}`)
    
    try {
      const encodedTitle = encodeURIComponent(title)
      const searchUrl = URLS.WIKIPEDIA_SEARCH.replace('{keyword}', encodedTitle)
      
      const html = await this.httpClient.get<string>(searchUrl)
      const $ = cheerio.load(html)
      
      // 查找第一个结果链接
      const resultLink = $('div.mw-search-result-heading a').first()
      if (!resultLink.length) {
        log.info('[Wikipedia] No search results')
        return null
      }
      
      const resultTitle = resultLink.text().trim()
      const resultHref = resultLink.attr('href') || ''
      const articleUrl = URLS.WIKIPEDIA_BASE + resultHref
      
      log.info(`[Wikipedia] Found article: ${resultTitle}`)
      
      // 获取文章页面以获取封面图片
      const articleHtml = await this.httpClient.get<string>(articleUrl)
      const $article = cheerio.load(articleHtml)
      
      // 尝试在 infobox 中找图片
      let coverUrl: string | undefined
      const infobox = $article('table.infobox').first()
      
      if (infobox.length) {
        const firstImg = infobox.find('img').first()
        if (firstImg.length) {
          const src = firstImg.attr('src') || ''
          if (src) {
            coverUrl = this.fixWikipediaUrl(src)
          }
        }
      }
      
      // 如果没有在 infobox 找到，尝试查找 File 链接
      if (!coverUrl) {
        const fileLink = $article('a.image[href*="File:"]').first()
        if (fileLink.length) {
          const fileHref = fileLink.attr('href') || ''
          const fileUrl = URLS.WIKIPEDIA_BASE + fileHref
          const fileHtml = await this.httpClient.get<string>(fileUrl)
          const $file = cheerio.load(fileHtml)
          
          const img = $file('img[typeof="mw:File"]').first() || $file('div#file img').first()
          if (img.length) {
            const src = img.attr('src') || img.attr('data-src') || ''
            if (src) {
              coverUrl = this.fixWikipediaUrl(src)
            }
          }
        }
      }
      
      if (!coverUrl) {
        log.info('[Wikipedia] No cover image found')
        return null
      }
      
      log.info(`[Wikipedia] Found cover: ${coverUrl.substring(0, 60)}...`)
      
      return {
        title: resultTitle,
        subjectUrl: articleUrl,
        coverUrl,
        rating: undefined,
        rank: undefined,
        type: 'unknown',
        date: undefined,
        summary: undefined,
        genres: [],
        staff: [],
        cast: []
      }
    } catch (error) {
      log.warn('[Wikipedia] Search failed:', error)
      return null
    }
  }

  /**
   * 修复 Wikipedia 图片 URL
   */
  private fixWikipediaUrl(url: string): string {
    if (!url) return ''
    
    // 添加协议
    if (url.startsWith('//')) {
      url = 'https:' + url
    }
    
    // 尝试获取更大的图片版本
    // Wikipedia URL 格式: //upload.wikimedia.org/wikipedia/commons/thumb/xxx/yyy/zzz.jpg/320px-zzz.jpg
    if (url.includes('/thumb/')) {
      // 移除缩略图尺寸前缀，获取原图
      url = url.replace(/\/\d+px-[^/]+$/, '')
    }
    
    return url
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
      
      // 构建封面URL（处理各种格式）
      let coverUrl: string | undefined
      const images = data.images || {}
      const rawCoverUrl = images.common || images.large || images.medium || images.small
      
      if (rawCoverUrl) {
        coverUrl = this.fixCoverUrl(rawCoverUrl)
      }
      
      const info: BangumiInfo = {
        title: data.name_cn || data.name,
        subjectUrl: `${URLS.BANGUMI_BASE}/subject/${subjectId}`,
        coverUrl,
        rating: data.rating?.score,
        rank: data.rank,
        type: this.mapType(data.type),
        date: data.air_date,
        summary: data.summary,
        genres: data.tags?.map((t: any) => t.name).slice(0, 10) || [],
        staff: [],
        cast: []
      }
      
      // 提取 staff
      if (data.staff) {
        info.staff = data.staff.slice(0, 10).map((s: any) => ({
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
   * 修复封面URL格式
   * 处理 //xxx, https:http:// 等各种格式问题
   */
  private fixCoverUrl(url: string): string {
    if (!url) return ''
    
    // 移除首尾空白
    url = url.trim()
    
    // 处理 // 开头的协议相对URL
    if (url.startsWith('//')) {
      return 'https:' + url
    }
    
    // 处理 https:http:// 这种格式错误
    if (url.startsWith('https:http')) {
      url = url.replace('https:http', 'http')
    }
    if (url.startsWith('http:https')) {
      url = url.replace('http:https', 'https')
    }
    
    // 如果没有协议，添加 https://
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url
    }
    
    return url
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

// 便捷函数
export async function findBangumiCover(
  title: string,
  year?: string,
  season?: string
): Promise<{ coverUrl: string | null; info: BangumiInfo | null }> {
  const crawler = new BangumiCrawler()
  try {
    const result = await crawler.findBestMatch(title, year, season)
    if (result) {
      return { coverUrl: result.info.coverUrl || null, info: result.info }
    }
    return { coverUrl: null, info: null }
  } finally {
    crawler.close()
  }
}
