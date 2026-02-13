/**
 * Anime1.me 爬虫
 * 
 * 对应原项目: src/parser/anime1_parser.py
 */

import * as cheerio from 'cheerio'
import log from 'electron-log'
import type { Anime, Episode } from '@shared/types'
import { URLS, PATTERNS } from '@shared/constants'
import { HttpClient, createAnime1HttpClient } from './http-client'

export class Anime1Crawler {
  private httpClient: HttpClient

  constructor(httpClient?: HttpClient) {
    this.httpClient = httpClient ?? createAnime1HttpClient()
  }

  /**
   * 获取番剧列表
   * 对应: src/parser/anime1_parser.py - parse_page / parse_anime_list
   */
  async fetchAnimeList(): Promise<Anime[]> {
    log.info('[Anime1] Fetching anime list...')
    
    // axios 会自动解析 JSON，所以直接获取 any 类型
    const data = await this.httpClient.get<any[]>(URLS.ANIME1_API)
    const animeList = this.parseAnimeData(data)
    
    log.info(`[Anime1] Fetched ${animeList.length} anime`)
    return animeList
  }

  /**
   * 解析番剧列表
   */
  private parseAnimeData(data: any[]): Anime[] {
    const animeList: Anime[] = []
    const seenIds = new Set<string>()

    try {
      if (!Array.isArray(data)) {
        log.warn('[Anime1] Response is not an array')
        return animeList
      }
      
      for (const item of data) {
        if (!Array.isArray(item) || item.length < 2) continue

        const catId = String(item[0])
        const titleRaw = String(item[1])
        
        // 提取纯文本标题
        const title = this.extractTitle(titleRaw)
        if (!title) continue

        // 跳过重复
        const uniqueId = this.generateId(catId, title)
        if (seenIds.has(uniqueId)) continue
        seenIds.add(uniqueId)

        // 提取集数
        const episodeStr = item[2] ? String(item[2]) : '0'
        const episodeMatch = episodeStr.match(/\((\d+)\)/)
        const episode = episodeMatch ? parseInt(episodeMatch[1], 10) : 0

        // 提取年份、季节、字幕组（如果有）
        const year = item[3] ? String(item[3]) : ''
        const season = item[4] ? String(item[4]) : ''
        const subtitleGroup = item[5] ? String(item[5]) : ''

        // 构建详情 URL
        let detailUrl: string
        if (catId === '0' || !catId) {
          // anime1.pw 外链
          const linkMatch = titleRaw.match(/href="([^"]+)"/)
          if (!linkMatch) continue
          detailUrl = linkMatch[1]
        } else {
          detailUrl = `${URLS.ANIME1_BASE}/?cat=${catId}`
        }

        animeList.push({
          id: uniqueId,
          title,
          detailUrl,
          episode,
          year,
          season,
          subtitleGroup,
          coverUrl: '',
          matchScore: 0,
          matchSource: ''
        })
      }
    } catch (error) {
      log.error('[Anime1] Failed to parse anime list:', error)
    }

    return animeList
  }

  /**
   * 从 HTML 解析番剧列表（备用方法）
   */
  private parseAnimeListFromHtml(html: string): Anime[] {
    const $ = cheerio.load(html)
    const animeList: Anime[] = []

    $('li.item a.subjectCover').each((_, elem) => {
      const $elem = $(elem)
      const title = $elem.attr('title') || ''
      const href = $elem.attr('href') || ''
      
      // 提取 ID
      const idMatch = href.match(/\/?cat=(\d+)/)
      const id = idMatch ? idMatch[1] : ''
      
      if (!id || !title) return

      animeList.push({
        id,
        title,
        detailUrl: href.startsWith('http') ? href : `${URLS.ANIME1_BASE}${href}`,
        episode: 0,
        coverUrl: '',
        year: '',
        season: '',
        subtitleGroup: '',
        matchScore: 0,
        matchSource: ''
      })
    })

    return animeList
  }

  /**
   * 提取标题（去除 HTML 标签）
   */
  private extractTitle(titleRaw: string): string {
    // 移除 HTML 标签
    let title = titleRaw.replace(/<[^>]+>/g, '').trim()
    
    // 解码 HTML 实体
    const entities: Record<string, string> = {
      '&amp;': '&',
      '&lt;': '<',
      '&gt;': '>',
      '&quot;': '"',
      '&#39;': "'"
    }
    
    for (const [entity, char] of Object.entries(entities)) {
      title = title.replace(new RegExp(entity, 'g'), char)
    }
    
    return title.trim()
  }

  /**
   * 生成唯一 ID
   */
  private generateId(catId: string, title: string): string {
    if (catId && catId !== '0') {
      return catId
    }
    // 对于 anime1.pw 外链，使用标题哈希
    let hash = 0
    for (let i = 0; i < title.length; i++) {
      const char = title.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return String(Math.abs(hash) % 1000000)
  }

  /**
   * 获取番剧详情
   * 对应: src/parser/anime1_parser.py - parse_anime_detail
   */
  async fetchAnimeDetail(url: string): Promise<{
    year: string
    season: string
    subtitleGroup: string
  }> {
    log.info(`[Anime1] Fetching anime detail: ${url}`)
    
    const html = await this.httpClient.get<string>(url)
    const $ = cheerio.load(html)
    
    // 提取页面文本
    const text = $.text()
    
    return {
      year: this.extractYear(text),
      season: this.extractSeason(text),
      subtitleGroup: this.extractSubtitleGroup(text)
    }
  }

  /**
   * 提取年份
   */
  private extractYear(text: string): string {
    const match = text.match(PATTERNS.YEAR)
    return match ? match[0] : ''
  }

  /**
   * 提取季节
   */
  private extractSeason(text: string): string {
    const seasons = ['冬季', '春季', '夏季', '秋季']
    for (const season of seasons) {
      if (text.includes(season)) {
        return season
      }
    }
    return ''
  }

  /**
   * 提取字幕组
   */
  private extractSubtitleGroup(text: string): string {
    const keywords = ['字幕組', '字幕', '翻譯', '翻']
    for (const keyword of keywords) {
      if (text.includes(keyword)) {
        // 尝试提取字幕组名称
        const patterns = [
          new RegExp(`([^\\s【】]+)${keyword}`),
          new RegExp(`${keyword}[:：]?\\s*([^\\s]+)`)
        ]
        for (const pattern of patterns) {
          const match = text.match(pattern)
          if (match) {
            return match[1] || match[0]
          }
        }
        return keyword
      }
    }
    return ''
  }

  /**
   * 获取剧集列表
   * 对应: src/parser/anime1_parser.py - parse_episode_list / _extract_episodes
   */
  async fetchEpisodes(detailUrl: string): Promise<Episode[]> {
    log.info(`[Anime1] Fetching episodes: ${detailUrl}`)
    
    const episodes: Episode[] = []
    const seenIds = new Set<string>()
    
    // 获取第一页
    const firstPageHtml = await this.httpClient.get<string>(detailUrl)
    const firstPageEpisodes = this.extractEpisodes(firstPageHtml)
    
    for (const ep of firstPageEpisodes) {
      if (!seenIds.has(ep.id)) {
        seenIds.add(ep.id)
        episodes.push(ep)
      }
    }
    
    // 获取总页数
    const totalPages = this.getTotalEpisodePages(firstPageHtml)
    
    // 限制最大页数
    const maxPages = Math.min(totalPages, 5)
    
    // 获取后续页面
    for (let page = 2; page <= maxPages; page++) {
      try {
        const pageUrl = this.buildPageUrl(detailUrl, page)
        const pageHtml = await this.httpClient.get<string>(pageUrl)
        const pageEpisodes = this.extractEpisodes(pageHtml)
        
        for (const ep of pageEpisodes) {
          if (!seenIds.has(ep.id)) {
            seenIds.add(ep.id)
            episodes.push(ep)
          }
        }
      } catch (error) {
        log.warn(`[Anime1] Failed to fetch page ${page}:`, error)
        break
      }
    }
    
    // 按集数降序排列（最新的在前）
    episodes.sort((a, b) => {
      const numA = parseFloat(a.episode) || 0
      const numB = parseFloat(b.episode) || 0
      return numB - numA
    })
    
    log.info(`[Anime1] Fetched ${episodes.length} episodes`)
    return episodes
  }

  /**
   * 提取剧集
   */
  private extractEpisodes(html: string): Episode[] {
    const $ = cheerio.load(html)
    const episodes: Episode[] = []
    
    // 标准列表格式: <h2 class="entry-title"><a href="https://anime1.me/27788">Title [37]</a></h2>
    $('h2.entry-title a[href*="/"]').each((_, elem) => {
      const $elem = $(elem)
      const href = $elem.attr('href') || ''
      const titleText = $elem.text().trim()
      
      // 跳过分类链接
      if (href.includes('/?cat=') || href.includes('/category/')) {
        return
      }
      
      // 提取剧集 ID
      const idMatch = href.match(/\/(\d+)$/)
      if (!idMatch) return
      const episodeId = idMatch[1]
      
      // 提取集数序号 [N] 格式
      const epMatch = titleText.match(/\[(\d+(?:\.\d+)?)\]$/)
      if (!epMatch) return
      const episodeNum = epMatch[1]
      
      // 清理标题
      const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, '').trim()
      
      // 提取日期
      const $article = $elem.closest('article')
      const date = $article.find('time.entry-date').text().trim()
      
      episodes.push({
        id: episodeId,
        title,
        episode: episodeNum,
        url: href,
        date
      })
    })
    
    // 如果没有找到，检查是否是单集页面
    if (episodes.length === 0) {
      const singleEpisode = this.extractSingleEpisode(html)
      if (singleEpisode) {
        episodes.push(singleEpisode)
      }
    }
    
    return episodes
  }

  /**
   * 提取单集（剧场版或单集页面）
   */
  private extractSingleEpisode(html: string): Episode | null {
    const $ = cheerio.load(html)
    
    // 检查是否是单篇文章页面
    const $article = $('article.post')
    if (!$article.length) return null
    
    // 必须有视频标签
    const $video = $('video')
    if (!$video.length) return null
    
    // 提取标题
    const titleText = $('h2.entry-title').text().trim()
    const title = titleText.replace(/\s*\[\d+(?:\.\d+)?\]\s*$/, '').trim()
    
    // 提取日期
    const date = $('time.entry-date').text().trim()
    
    // 从文章 class 提取 ID (e.g., "post-27546")
    let episodeId = ''
    const classAttr = $article.attr('class') || ''
    const idMatch = classAttr.match(/post-(\d+)/)
    if (idMatch) {
      episodeId = idMatch[1]
    }
    
    // 从 canonical 链接提取
    if (!episodeId) {
      const canonical = $('link[rel="canonical"]').attr('href') || ''
      const urlMatch = canonical.match(/\/(\d+)$/)
      if (urlMatch) {
        episodeId = urlMatch[1]
      }
    }
    
    if (!episodeId) return null
    
    return {
      id: episodeId,
      title: title || 'Unknown',
      episode: '1',
      url: `${URLS.ANIME1_BASE}/${episodeId}`,
      date
    }
  }

  /**
   * 获取总页数
   */
  private getTotalEpisodePages(html: string): number {
    const $ = cheerio.load(html)
    let maxPage = 1
    
    $('a[href*="/page/"]').each((_, elem) => {
      const href = $(elem).attr('href') || ''
      const match = href.match(/\/page\/(\d+)/)
      if (match) {
        const pageNum = parseInt(match[1], 10)
        maxPage = Math.max(maxPage, pageNum)
      }
    })
    
    return maxPage
  }

  /**
   * 构建分页 URL
   */
  private buildPageUrl(detailUrl: string, page: number): string {
    if (detailUrl.includes('/category/')) {
      const parts = detailUrl.split('/category/')
      return `${parts[0]}/category/${parts[1]}/page/${page}`
    } else if (detailUrl.includes('?cat=')) {
      return `${detailUrl}&page=${page}`
    } else {
      return `${detailUrl}?page=${page}`
    }
  }

  /**
   * 关闭爬虫
   */
  close(): void {
    this.httpClient.close()
    log.info('[Anime1] Crawler closed')
  }
}
