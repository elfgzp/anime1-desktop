/**
 * Bangumi 爬虫 - 完全对应 Python 版本实现
 * 
 * Python 参考: src/parser/cover_finder.py
 */

import * as cheerio from 'cheerio'
import log from 'electron-log'
import * as OpenCC from 'opencc-js'
import type { BangumiInfo, BangumiSearchResult } from '@shared/types'
import { URLS } from '@shared/constants'
import { HttpClient, createDefaultHttpClient } from './http-client'

// 与 Python config.py 完全一致的常量
const CONFIG = {
  MIN_MATCH_SCORE: 30,
  MIN_TITLE_LENGTH: 4,
  MIN_CHINESE_CHARS: 2,
  SCORE_EXACT: 100,
  SCORE_CONTAINS: 90,
  SCORE_SUBSTRING: 85,
  SCORE_WORD_OVERLAP: 50,
  SCORE_CHINESE_OVERLAP: 40,
  MAX_KEYWORD_LENGTH: 15,
}

// URL 常量
const URL_PREFIX_HTTPS = 'https:'
const URL_BANGUMI_BASE = 'https://bangumi.tv'

export class BangumiCrawler {
  private httpClient: HttpClient
  private t2sConverter: any

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createDefaultHttpClient()
    try {
      this.t2sConverter = OpenCC.Converter({ from: 'tw', to: 'cn' })
    } catch (e) {
      log.warn('[Bangumi] OpenCC init failed:', e)
    }
  }

  /**
   * 转换为简体中文（与 Python: _to_simplified_chinese 一致）
   */
  private toSimplified(text: string): string {
    if (!this.t2sConverter || !text) return text
    try {
      return this.t2sConverter(text)
    } catch (e) {
      return text
    }
  }

  /**
   * 主搜索方法（与 Python: _search_bangumi 完全一致）
   */
  async findBestMatch(
    title: string,
    _year?: string
  ): Promise<{ info: BangumiInfo; score: number } | null> {
    log.info(`[Bangumi] Finding best match for: ${title}`)

    // 收集所有搜索结果
    let allResults: Array<{ result: BangumiSearchResult; score: number }> = []

    // 策略1: 尝试原（繁体）标题和简体标题搜索，合并结果
    const titleSimplified = this.toSimplified(title)

    // 使用原标题搜索
    const originalResults = await this.searchWithKeywordMulti(title, title)
    allResults = allResults.concat(originalResults)

    // 如果简体不同，也用简体搜索
    if (titleSimplified && titleSimplified !== title) {
      const simplifiedResults = await this.searchWithKeywordMulti(titleSimplified, title)
      // 合并，避免重复
      for (const r of simplifiedResults) {
        if (!allResults.find(existing => existing.result.id === r.result.id)) {
          allResults.push(r)
        }
      }
    }

    // 策略2: 如果完整标题没有好的匹配，尝试核心关键词
    const hasGoodMatch = allResults.some(r => r.score >= CONFIG.MIN_MATCH_SCORE)

    if (!hasGoodMatch) {
      const coreKeywords = this.extractCoreKeywords(title)
      if (coreKeywords && coreKeywords !== title) {
        const coreSimplified = this.toSimplified(coreKeywords)

        // 核心关键词原搜索
        const coreOriginalResults = await this.searchWithKeywordMulti(coreKeywords, title)
        for (const r of coreOriginalResults) {
          if (!allResults.find(existing => existing.result.id === r.result.id)) {
            allResults.push(r)
          }
        }

        // 核心关键词简体搜索
        if (coreSimplified && coreSimplified !== coreKeywords) {
          const coreSimplifiedResults = await this.searchWithKeywordMulti(coreSimplified, title)
          for (const r of coreSimplifiedResults) {
            if (!allResults.find(existing => existing.result.id === r.result.id)) {
              allResults.push(r)
            }
          }
        }
      }
    }

    if (allResults.length === 0) {
      log.info('[Bangumi] No search results')
      return null
    }

    // 按分数排序
    allResults.sort((a, b) => b.score - a.score)

    // 选择最佳匹配
    const bestMatch = allResults[0]
    log.info(`[Bangumi] Best match: ${bestMatch.result.title} (score: ${bestMatch.score})`)

    // 获取详细信息
    const info = await this.getSubjectInfo(bestMatch.result.id, bestMatch.result.coverUrl)
    if (!info) {
      return null
    }

    // 如果分数低于阈值，标记为低置信度
    if (bestMatch.score < CONFIG.MIN_MATCH_SCORE) {
      log.info(`[Bangumi] Low confidence match (score: ${bestMatch.score} < ${CONFIG.MIN_MATCH_SCORE})`)
      return { info, score: 0 }
    }

    return { info, score: bestMatch.score }
  }

  /**
   * 使用关键词搜索并返回多个评分结果（与 Python: _search_with_keyword_multi 一致）
   * 
   * 重要：不要对中文关键词进行 URL 编码！
   * Bangumi 服务器对编码和未编码的中文返回不同结果，
   * 未编码的中文能得到更准确的搜索结果。
   */
  private async searchWithKeywordMulti(
    keyword: string,
    originalTitle: string
  ): Promise<Array<{ result: BangumiSearchResult; score: number }>> {
    if (!keyword) return []

    // 清理关键词（与 Python: re.sub(PATTERNS["non_word_chars"], "", keyword) 一致）
    // 注意：Python \w 匹配 Unicode，JavaScript 需要显式包含中文
    const cleanedKeyword = keyword.replace(/[^\w\s\u4e00-\u9fa5]/g, '').trim()
    if (!cleanedKeyword) return []

    // 关键：不编码中文，直接放在 URL 中
    // axios 会自动处理编码，但我们需要保留中文以获得更好的搜索结果
    const url = `${URL_BANGUMI_BASE}/subject_search/${cleanedKeyword}?cat=2`

    try {
      log.info(`[Bangumi] GET ${url}`)
      const html = await this.httpClient.get<string>(url)
      const $ = cheerio.load(html)
      const items = $('#browserItemList li.item')

      if (!items.length) return []

      // 比较时使用简体（关键！与 Python 第 197-200 行一致）
      let compareTitle = this.toSimplified(originalTitle)

      return this.scoreAllResults(compareTitle, $, items)
    } catch (error) {
      log.warn(`[Bangumi] Search failed for "${keyword}":`, error)
      return []
    }
  }

  /**
   * 评分所有搜索结果（与 Python: _score_all_results 一致）
   */
  private scoreAllResults(
    originalTitle: string,
    $: cheerio.CheerioAPI,
    items: any
  ): Array<{ result: BangumiSearchResult; score: number }> {
    const results: Array<{ result: BangumiSearchResult; score: number }> = []

    items.each((_index: any, elem: any) => {
      const $elem = $(elem)

      // 提取标题（与 Python: name_elem.get_text(strip=True) 一致）
      const nameElem = $elem.find('h3 a')
      const resultName = nameElem.text().trim()

      if (!resultName) return

      // 清理标题并检查长度（与 Python 第 228-231 行一致）
      // 注意：Python \w 匹配 Unicode，JavaScript 需要显式包含中文
      const resultNameClean = resultName.replace(/[^\w\s\u4e00-\u9fa5]/g, '').trim()
      let score: number

      if (resultNameClean.length < CONFIG.MIN_TITLE_LENGTH) {
        score = 0
      } else {
        score = this.calculateTitleSimilarity(originalTitle, resultName)
      }

      // 提取封面（与 Python: _extract_cover_from_item 一致）
      const coverUrl = this.extractCoverFromItem($elem)
      if (!coverUrl) return

      // 提取 ID
      const href = nameElem.attr('href') || ''
      const idMatch = href.match(/\/subject\/(\d+)/)
      if (!idMatch) return

      const id = parseInt(idMatch[1], 10)

      // 提取中文标题
      const titleCn = $elem.find('.subjectTitle .tip').text().trim() || undefined

      results.push({
        result: {
          id,
          title: resultName,
          titleCn,
          coverUrl
        },
        score
      })
    })

    // 按分数降序排序
    results.sort((a, b) => b.score - a.score)
    return results
  }

  /**
   * 计算标题相似度（与 Python: _calculate_title_similarity 完全一致）
   */
  private calculateTitleSimilarity(query: string, result: string): number {
    if (!query || !result) return 0

    // 清理标题（与 Python 第 744-745 行一致）
    const queryClean = query.replace(/[【】\(\)（）\[\]!!！\s～~？?]/g, '').trim()
    const resultClean = result.replace(/[【】\(\)（）\[\]!!！\s～~？?]/g, '').trim()

    // 完全匹配
    if (queryClean === resultClean) {
      return CONFIG.SCORE_EXACT
    }

    // 包含匹配
    if (queryClean.includes(resultClean) || resultClean.includes(queryClean)) {
      return CONFIG.SCORE_SUBSTRING
    }

    // 核心匹配（与 Python 第 756-766 行一致）
    // 注意：Python 这里是对 clean title 使用 _extract_core_keywords
    // 但 clean title 已经移除了括号，所以这里效果相同
    const queryCore = this.extractCoreKeywords(query)
    const resultCore = this.extractCoreKeywords(result)

    if (queryCore && resultCore && queryCore === resultCore) {
      return CONFIG.SCORE_CONTAINS
    }

    if (queryCore && resultCore) {
      if (queryCore.includes(resultCore) || resultCore.includes(queryCore)) {
        return CONFIG.SCORE_SUBSTRING - 5
      }
    }

    // 中文字符重叠（与 Python 第 770-785 行一致）
    const c1 = new Set(queryClean.split('').filter(c => /[\u4e00-\u9fff]/.test(c)))
    const c2 = new Set(resultClean.split('').filter(c => /[\u4e00-\u9fff]/.test(c)))

    if (c1.size > 0 && c2.size > 0) {
      const overlap = new Set([...c1].filter(x => c2.has(x)))
      const total = Math.max(c1.size, c2.size)

      if (total > 0) {
        const ratio = overlap.size / total
        if (ratio >= 0.5) {
          return Math.floor(ratio * CONFIG.SCORE_EXACT)
        } else if (ratio >= 0.3) {
          return Math.floor(ratio * CONFIG.SCORE_CONTAINS)
        } else if (ratio >= 0.2 && overlap.size >= 3) {
          return CONFIG.SCORE_CHINESE_OVERLAP
        }
      }
    }

    // 字符重叠（与 Python 第 788-796 行一致）
    const queryWords = new Set(queryClean)
    const resultWords = new Set(resultClean)

    if (queryWords.size > 0 && resultWords.size > 0) {
      const common = new Set([...queryWords].filter(x => resultWords.has(x)))
      const total = new Set([...queryWords, ...resultWords])

      if (total.size > 0) {
        const ratio = common.size / total.size
        if (ratio >= 0.3) {
          return Math.floor(ratio * CONFIG.SCORE_WORD_OVERLAP)
        }
      }
    }

    return 0
  }

  /**
   * 提取核心关键词（与 Python: _extract_core_keywords 一致）
   */
  private extractCoreKeywords(title: string): string {
    if (!title) return ''

    // 移除括号内容（保留季节信息）
    let core = title.replace(/[【】\(\)（）\[\]～~].*$/, '')
    core = core.trim()

    return core || title
  }

  /**
   * 从列表项提取封面（与 Python: _extract_cover_from_item 一致）
   */
  private extractCoverFromItem($elem: any): string | undefined {
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
   * 
   * Bangumi 图片 URL 格式：
   * - //lain.bgm.tv/pic/cover/c/xx/xx/xxxx.jpg - 普通图
   * - //lain.bgm.tv/pic/cover/l/xx/xx/xxxx.jpg - 大图
   * - //lain.bgm.tv/r/400/pic/cover/l/xx/xx/xxxx.jpg - 400px缩略图
   * 
   * 目标：获取高清大图，移除 /r/xxx/ 尺寸限制
   */
  private normalizeCoverUrl(url: string): string {
    if (!url) return ''

    // 添加协议
    if (url.startsWith('//')) {
      url = URL_PREFIX_HTTPS + url
    } else if (url.startsWith('/')) {
      url = URL_BANGUMI_BASE + url
    }

    // 移除 /r/xxx/ 缩略图限制，获取原图
    url = url.replace(/\/r\/\d+\//, '/')

    // 转换为高清大图 /l/
    url = url.replace(/\/pic\/cover\/[cms]\//, '/pic/cover/l/')

    return url
  }

  /**
   * 获取 Bangumi 详细信息（使用 API）
   */
  async getSubjectInfo(subjectId: number, coverUrlFromSearch?: string): Promise<BangumiInfo | null> {
    log.info(`[Bangumi] Getting subject info: ${subjectId}`)

    try {
      const url = `${URLS.BANGUMI_API}/subject/${subjectId}?responseGroup=large`
      const data = await this.httpClient.get<any>(url)

      if (!data || data.type !== 2) {
        return null
      }

      // 优先使用搜索得到的封面 URL（需要标准化）
      let coverUrl = coverUrlFromSearch ? this.normalizeCoverUrl(coverUrlFromSearch) : ''

      // 如果没有，从 API 获取
      if (!coverUrl) {
        const images = data.images || {}
        // 优先使用 large（大图），其次 common（普通图）
        const rawUrl = images.large || images.common
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
  year?: string
): Promise<{ coverUrl: string | null; info: BangumiInfo | null }> {
  const crawler = new BangumiCrawler()
  try {
    const result = await crawler.findBestMatch(title, year)
    if (result) {
      return { coverUrl: result.info.coverUrl || null, info: result.info }
    }
    return { coverUrl: null, info: null }
  } finally {
    crawler.close()
  }
}
