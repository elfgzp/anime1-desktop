/**
 * Bangumi 爬虫 - 完整对应 Python 版本实现
 * 
 * Python 参考: src/parser/cover_finder.py
 * 主要改动:
 * - 使用 HTML 页面搜索（而非 API）作为主要方式
 * - 封面 URL 直接来自列表页
 * - 保留 API 作为 fallback
 */

import * as cheerio from 'cheerio'
import log from 'electron-log'
import * as OpenCC from 'opencc-js'
import type { BangumiInfo, BangumiSearchResult } from '@shared/types'
import { URLS, BANGUMI_CONFIG } from '@shared/constants'
import { HttpClient, createDefaultHttpClient } from './http-client'

// 匹配配置（与 Python 完全一致）
const MATCH_CONFIG = {
  MIN_MATCH_SCORE: 30,
  YEAR_MATCH_BONUS: 15,
  YEAR_MISMATCH_PENALTY: 10,
}

// Bangumi 封面质量（Python: BANGUMI_COVER_QUALITY = "common"）
const COVER_QUALITY = 'common'

export class BangumiCrawler {
  private httpClient: HttpClient
  private t2sConverter: any
  private s2tConverter: any

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createDefaultHttpClient()
    try {
      this.t2sConverter = OpenCC.Converter({ from: 'tw', to: 'cn' })
      this.s2tConverter = OpenCC.Converter({ from: 'cn', to: 'tw' })
    } catch (e) {
      log.warn('[Bangumi] OpenCC init failed:', e)
    }
  }

  private toSimplified(text: string): string {
    if (!this.t2sConverter) return text
    try {
      return this.t2sConverter(text)
    } catch (e) {
      return text
    }
  }

  private toTraditional(text: string): string {
    if (!this.s2tConverter) return text
    try {
      return this.s2tConverter(text)
    } catch (e) {
      return text
    }
  }

  /**
   * 获取标题的各种变体（与 Python: _get_search_variants 一致）
   */
  private getTitleVariants(title: string): string[] {
    const variants = new Set<string>([title])
    
    const traditional = this.toTraditional(title)
    if (traditional !== title) {
      variants.add(traditional)
    }
    
    const simplified = this.toSimplified(title)
    if (simplified !== title) {
      variants.add(simplified)
    }
    
    return Array.from(variants)
  }

  /**
   * 提取核心关键词（与 Python: _extract_core_keywords 一致）
   */
  private extractCoreKeyword(title: string): string {
    if (!title) return ""
    
    // 移除括号内容（但保留季节信息）
    let core = title.replace(/[【】\(\)（）\[\]～~].*?$/, "")
    core = core.trim()
    
    return core || title
  }

  /**
   * 截断关键词（与 Python: _truncate_keywords 一致）
   */
  private truncateKeywords(keywords: string): string {
    const MAX_KEYWORD_LENGTH = 15
    
    if (!keywords) return ""
    
    // 移除特殊字符
    const cleaned = keywords.replace(/[【】\(\)（）\[\]～~!！\?]/g, "").trim()
    
    if (cleaned.length <= MAX_KEYWORD_LENGTH) {
      return cleaned
    }
    
    // 截断到最大长度
    const truncated = cleaned.substring(0, MAX_KEYWORD_LENGTH * 2)
    
    // 找到最后一个完整词边界
    const parts = truncated.split(/[\s,，、]/)
    if (parts.length > 1) {
      const result = parts.slice(0, -1).join(" ")
      if (result) return result.trim()
    }
    
    return cleaned.substring(0, MAX_KEYWORD_LENGTH)
  }

  /**
   * 主搜索方法（与 Python: search_bangumi / _search_with_keyword_multi 一致）
   * 使用 HTML 页面搜索
   */
  async searchByTitle(title: string): Promise<BangumiSearchResult[]> {
    log.info(`[Bangumi] Searching HTML: ${title}`)
    
    const allResults: BangumiSearchResult[] = []
    const seenIds = new Set<number>()
    
    // 获取所有搜索变体
    const variants = this.getTitleVariants(title)
    
    for (const variant of variants) {
      if (!variant.trim()) continue
      
      try {
        const results = await this.searchHtml(variant)
        
        for (const result of results) {
          if (!seenIds.has(result.id)) {
            seenIds.add(result.id)
            allResults.push(result)
          }
        }
      } catch (error) {
        log.warn(`[Bangumi] HTML search failed for "${variant}":`, error)
      }
    }
    
    return allResults
  }

  /**
   * HTML 页面搜索（与 Python: _search_with_keyword_multi 一致）
   */
  private async searchHtml(keyword: string): Promise<BangumiSearchResult[]> {
    try {
      // URL 编码关键词
      const encodedKeyword = encodeURIComponent(keyword)
      const searchUrl = `${URLS.BANGUMI_BASE}/subject_search/${encodedKeyword}?cat=2`
      
      log.info(`[Bangumi] GET ${searchUrl}`)
      const html = await this.httpClient.get<string>(searchUrl)
      const $ = cheerio.load(html)
      
      const results: BangumiSearchResult[] = []
      
      // 解析列表项（与 Python: soup.select("li.item") 一致）
      $('#browserItemList li.item').each((_, elem) => {
        const $elem = $(elem)
        
        // 提取链接和 ID
        const $link = $elem.find('h3 a')
        const href = $link.attr('href') || ''
        const idMatch = href.match(/\/subject\/(\d+)/)
        if (!idMatch) return
        
        const id = parseInt(idMatch[1], 10)
        
        // 提取标题（与 Python: name_elem.get_text(strip=True) 一致）
        const resultTitle = $link.text().trim()
        
        // 提取中文标题
        const titleCn = $elem.find('.subjectTitle .tip').text().trim()
        
        // 提取封面（与 Python: _extract_cover_from_item 一致）
        const coverUrl = this.extractCoverFromItem($elem)
        
        // 提取评分
        const scoreText = $elem.find('.rateInfo .smallStars').parent().text().trim()
        const score = scoreText ? parseFloat(scoreText) : undefined
        
        // 提取排名
        const rankText = $elem.find('.rank').text().trim()
        const rank = rankText ? parseInt(rankText.replace('#', '')) : undefined
        
        results.push({
          id,
          title: resultTitle,
          titleCn: titleCn || undefined,
          coverUrl,
          score,
          rank
        })
      })
      
      return results
    } catch (error) {
      log.error('[Bangumi] HTML search error:', error)
      return []
    }
  }

  /**
   * 从列表项提取封面（与 Python: _extract_cover_from_item 完全一致）
   */
  private extractCoverFromItem($elem: cheerio.Cheerio): string | undefined {
    const coverLink = $elem.find('a.subjectCover')
    if (!coverLink.length) return undefined
    
    const img = coverLink.find('img.cover')
    if (!img.length) return undefined
    
    const imgSrc = img.attr('src') || ''
    if (!imgSrc) return undefined
    
    return this.normalizeCoverUrl(imgSrc)
  }

  /**
   * 标准化封面 URL（与 Python: _normalize_cover_url 一致）
   * 去掉 /r/xxx/ 缩略图限制，获取原图
   */
  private normalizeCoverUrl(url: string): string {
    if (!url) return ''
    
    // 添加协议
    if (url.startsWith('//')) {
      url = 'https:' + url
    } else if (url.startsWith('/')) {
      url = 'https://bangumi.tv' + url
    }
    
    // 去掉 Bangumi 缩略图限制 /r/xxx/，获取原图
    // 例如: https://lain.bgm.tv/r/400/pic/cover/l/xxx.jpg
    // 改为: https://lain.bgm.tv/pic/cover/l/xxx.jpg
    url = url.replace(/\/r\/\d+\//, '/')
    
    return url
  }

  /**
   * 计算标题相似度（与 Python: _calculate_title_similarity / _calculate_match_score 一致）
   */
  private calculateMatchScore(queryTitle: string, result: BangumiSearchResult): number {
    const titles = [result.title, result.titleCn].filter(Boolean) as string[]
    let bestScore = 0
    
    for (const resultTitle of titles) {
      if (!resultTitle) continue
      
      const score = this.calculateTitleSimilarity(queryTitle, resultTitle)
      bestScore = Math.max(bestScore, score)
    }
    
    return bestScore
  }

  /**
   * 计算标题相似度（与 Python: _calculate_title_similarity 一致）
   */
  private calculateTitleSimilarity(query: string, result: string): number {
    const SCORE_EXACT = 100
    const SCORE_CONTAINS = 90
    const SCORE_SUBSTRING = 85
    const SCORE_WORD_OVERLAP = 50
    const SCORE_CHINESE_OVERLAP = 40
    
    if (!query || !result) return 0
    
    // 清理标题
    const cleanQuery = query.replace(/[【】\(\)（）\[\]!!！\s～~]/g, "").trim()
    const cleanResult = result.replace(/[【】\(\)（）\[\]!!！\s～~]/g, "").trim()
    
    // 完全匹配
    if (cleanQuery === cleanResult) {
      return SCORE_EXACT
    }
    
    // 包含匹配
    if (cleanQuery.includes(cleanResult) || cleanResult.includes(cleanQuery)) {
      return SCORE_SUBSTRING
    }
    
    // 核心匹配
    const queryCore = this.extractCoreKeyword(cleanQuery)
    const resultCore = this.extractCoreKeyword(cleanResult)
    
    if (queryCore && resultCore && queryCore === resultCore) {
      return SCORE_CONTAINS
    }
    
    if (queryCore && resultCore) {
      if (queryCore.includes(resultCore) || resultCore.includes(queryCore)) {
        return SCORE_SUBSTRING - 5
      }
    }
    
    // 中文字符重叠
    const queryChars = new Set(cleanQuery.split('').filter(c => /[\u4e00-\u9fff]/.test(c)))
    const resultChars = new Set(cleanResult.split('').filter(c => /[\u4e00-\u9fff]/.test(c)))
    
    if (queryChars.size >= 2 && resultChars.size >= 2) {
      const overlap = new Set([...queryChars].filter(c => resultChars.has(c)))
      const total = new Set([...queryChars, ...resultChars])
      
      if (total.size > 0) {
        const ratio = overlap.size / total.size
        if (ratio >= 0.5) {
          return Math.floor(ratio * SCORE_EXACT)
        } else if (ratio >= 0.3) {
          return Math.floor(ratio * SCORE_CONTAINS)
        } else if (ratio >= 0.2 && overlap.size >= 3) {
          return SCORE_CHINESE_OVERLAP
        }
      }
    }
    
    // 字符重叠
    const querySet = new Set(cleanQuery)
    const resultSet = new Set(cleanResult)
    const common = new Set([...querySet].filter(c => resultSet.has(c)))
    
    if (common.size > 0) {
      const total = new Set([...querySet, ...resultSet])
      const ratio = common.size / total.size
      if (ratio >= 0.3) {
        return Math.floor(ratio * SCORE_WORD_OVERLAP)
      }
    }
    
    return 0
  }

  /**
   * 查找最佳匹配（与 Python: find_cover / _search_bangumi 一致）
   */
  async findBestMatch(
    title: string,
    year?: string,
    season?: string
  ): Promise<{ info: BangumiInfo; score: number } | null> {
    log.info(`[Bangumi] Finding best match for: ${title}`)
    
    // 1. 完整标题搜索
    const searchVariants = this.getTitleVariants(title)
    let allResults: BangumiSearchResult[] = []
    
    for (const variant of searchVariants) {
      const results = await this.searchByTitle(variant)
      for (const result of results) {
        if (!allResults.find(r => r.id === result.id)) {
          allResults.push(result)
        }
      }
    }
    
    // 2. 核心关键词搜索（如果没有好的匹配）
    const hasGoodMatch = allResults.some(r => this.calculateMatchScore(title, r) >= MATCH_CONFIG.MIN_MATCH_SCORE)
    
    if (!hasGoodMatch) {
      const coreKeyword = this.extractCoreKeyword(title)
      if (coreKeyword && coreKeyword !== title && coreKeyword.length >= 2) {
        log.info(`[Bangumi] Trying core keyword: ${coreKeyword}`)
        const coreVariants = this.getTitleVariants(coreKeyword)
        for (const variant of coreVariants) {
          const results = await this.searchByTitle(variant)
          for (const result of results) {
            if (!allResults.find(r => r.id === result.id)) {
              allResults.push(result)
            }
          }
        }
      }
    }
    
    if (allResults.length === 0) {
      log.info('[Bangumi] No search results')
      return null
    }
    
    // 3. 计算分数并排序
    const scoredResults = allResults.map(result => ({
      result,
      score: this.calculateMatchScore(title, result)
    }))
    
    scoredResults.sort((a, b) => b.score - a.score)
    
    // 4. 选择最佳匹配
    const bestMatch = scoredResults[0]
    log.info(`[Bangumi] Best match: ${bestMatch.result.title} (score: ${bestMatch.score})`)
    
    // 5. 获取详细信息（使用 API）
    const info = await this.getSubjectInfo(bestMatch.result.id, bestMatch.result.coverUrl)
    if (!info) {
      return null
    }
    
    // 低置信度匹配
    if (bestMatch.score < MATCH_CONFIG.MIN_MATCH_SCORE) {
      log.info(`[Bangumi] Low confidence match (score: ${bestMatch.score} < ${MATCH_CONFIG.MIN_MATCH_SCORE})`)
      return { info, score: 0 }
    }
    
    return { info, score: bestMatch.score }
  }

  /**
   * 获取 Bangumi 详细信息（使用 API）
   * 封面 URL 优先使用传入的（来自 HTML 搜索）
   */
  async getSubjectInfo(subjectId: number, coverUrlFromSearch?: string): Promise<BangumiInfo | null> {
    log.info(`[Bangumi] Getting subject info: ${subjectId}`)
    
    try {
      const url = `${URLS.BANGUMI_API}/subject/${subjectId}?responseGroup=large`
      const data = await this.httpClient.get<any>(url)
      
      if (!data || data.type !== 2) {
        return null
      }
      
      // 优先使用搜索得到的封面 URL
      let coverUrl = coverUrlFromSearch
      
      // 如果没有，从 API 获取
      if (!coverUrl) {
        const images = data.images || {}
        const rawUrl = images[COVER_QUALITY] || images.common || images.large
        if (rawUrl) {
          coverUrl = this.normalizeCoverUrl(rawUrl)
        }
      }
      
      const info: BangumiInfo = {
        title: data.name_cn || data.name,
        subjectUrl: `${URLS.BANGUMI_BASE}/subject/${subjectId}`,
        coverUrl,
        rating: data.rating?.score,
        rank: data.rank,
        type: 'anime',
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
      
      return info
    } catch (error) {
      log.error('[Bangumi] Failed to get subject info:', error)
      return null
    }
  }

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
