/**
 * 番剧服务
 * 
 * 对应原项目: src/services/anime_cache_service.py
 * 职责: 番剧数据管理、缓存、搜索
 */

import { EventEmitter } from 'events'
import log from 'electron-log'
import type { DatabaseService } from '../database'
import type { CrawlerService } from '../crawler'
import type { Anime, AnimePage, Episode, CacheStatus } from '@shared/types'
import { PAGINATION, CACHE_CONFIG } from '@shared/constants'

export class AnimeService extends EventEmitter {
  private databaseService: DatabaseService
  private crawlerService: CrawlerService
  private animeCache: Map<string, Anime> = new Map()
  private cacheInitialized = false
  private isRefreshing = false
  private refreshInterval: NodeJS.Timeout | null = null

  constructor(databaseService: DatabaseService, crawlerService: CrawlerService) {
    super()
    this.databaseService = databaseService
    this.crawlerService = crawlerService
  }

  /**
   * 初始化服务
   */
  async initialize(): Promise<void> {
    log.info('[AnimeService] Initializing...')
    
    // 加载番剧列表
    await this.loadAnimeList()
    
    // 启动后台刷新
    this.startBackgroundRefresh()
    
    this.cacheInitialized = true
    this.emit('initialized')
    
    log.info('[AnimeService] Initialized')
  }

  /**
   * 加载番剧列表
   */
  private async loadAnimeList(): Promise<void> {
    try {
      log.info('[AnimeService] Loading anime list...')
      
      const animeList = await this.crawlerService.fetchAnimeList()
      
      // 更新缓存
      this.animeCache.clear()
      for (const anime of animeList) {
        this.animeCache.set(anime.id, anime)
      }
      
      log.info(`[AnimeService] Loaded ${animeList.length} anime`)
      
      // 后台加载封面缓存
      this.loadCoverCachesInBackground()
    } catch (error) {
      log.error('[AnimeService] Failed to load anime list:', error)
      throw error
    }
  }

  /**
   * 后台加载封面缓存
   */
  private async loadCoverCachesInBackground(): Promise<void> {
    const animeList = Array.from(this.animeCache.values())
    
    // 分批处理，避免阻塞
    const batchSize = 5
    for (let i = 0; i < animeList.length; i += batchSize) {
      const batch = animeList.slice(i, i + batchSize)
      
      await Promise.all(
        batch.map(async (anime) => {
          try {
            // 检查是否有缓存
            const cached = this.databaseService.getCoverCache(anime.id)
            
            if (cached) {
              // 更新 anime 对象
              anime.coverUrl = cached.coverUrl
              anime.year = cached.year
              anime.season = cached.season
              anime.subtitleGroup = cached.subtitleGroup
              return
            }
            
            // 获取 Bangumi 信息
            const bangumiResult = await this.crawlerService.findBangumiInfo(
              anime.title,
              anime.year,
              anime.season
            )
            
            if (bangumiResult) {
              anime.coverUrl = bangumiResult.info.coverUrl || ''
              anime.matchScore = bangumiResult.score
              anime.matchSource = 'Bangumi'
              
              // 保存到数据库
              this.databaseService.setCoverCache(anime.id, {
                title: anime.title,
                coverUrl: anime.coverUrl,
                year: anime.year,
                season: anime.season,
                subtitleGroup: anime.subtitleGroup,
                episode: anime.episode
              }, bangumiResult.info)
            }
          } catch (error) {
            log.warn(`[AnimeService] Failed to load cover for ${anime.id}:`, error)
          }
        })
      )
      
      // 延迟，避免请求过快
      await this.sleep(1000)
    }
  }

  /**
   * 启动后台刷新
   */
  private startBackgroundRefresh(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
    
    this.refreshInterval = setInterval(async () => {
      try {
        await this.refreshCache()
      } catch (error) {
        log.error('[AnimeService] Background refresh failed:', error)
      }
    }, CACHE_CONFIG.REFRESH_INTERVAL)
    
    log.info('[AnimeService] Background refresh started')
  }

  /**
   * 停止后台刷新
   */
  stopBackgroundRefresh(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
      this.refreshInterval = null
      log.info('[AnimeService] Background refresh stopped')
    }
  }

  /**
   * 获取番剧列表（分页）
   */
  async getList(page: number, pageSize: number = PAGINATION.DEFAULT_PAGE_SIZE): Promise<AnimePage> {
    await this.ensureInitialized()
    
    const allAnime = Array.from(this.animeCache.values())
    const totalItems = allAnime.length
    const totalPages = Math.ceil(totalItems / pageSize)
    
    const startIdx = (page - 1) * pageSize
    const endIdx = startIdx + pageSize
    const pageAnime = allAnime.slice(startIdx, endIdx)
    
    return {
      animeList: pageAnime,
      currentPage: page,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1
    }
  }

  /**
   * 获取番剧详情
   */
  async getDetail(animeId: string): Promise<Anime> {
    await this.ensureInitialized()
    
    const anime = this.animeCache.get(animeId)
    if (!anime) {
      throw new Error(`Anime not found: ${animeId}`)
    }
    
    // 获取详细信息（年份、季节等）
    if (!anime.year || !anime.season) {
      try {
        const detail = await this.crawlerService.fetchAnimeDetail(anime.detailUrl)
        anime.year = detail.year || anime.year
        anime.season = detail.season || anime.season
        anime.subtitleGroup = detail.subtitleGroup || anime.subtitleGroup
      } catch (error) {
        log.warn(`[AnimeService] Failed to fetch detail for ${animeId}:`, error)
      }
    }
    
    // 获取封面（如果没有）
    if (!anime.coverUrl) {
      const bangumiResult = await this.crawlerService.findBangumiInfo(
        anime.title,
        anime.year,
        anime.season
      )
      
      if (bangumiResult) {
        anime.coverUrl = bangumiResult.info.coverUrl || ''
        anime.matchScore = bangumiResult.score
        anime.matchSource = 'Bangumi'
        
        this.databaseService.setCoverCache(anime.id, {
          title: anime.title,
          coverUrl: anime.coverUrl,
          year: anime.year,
          season: anime.season,
          subtitleGroup: anime.subtitleGroup,
          episode: anime.episode
        }, bangumiResult.info)
      }
    }
    
    return anime
  }

  /**
   * 获取剧集列表
   */
  async getEpisodes(animeId: string): Promise<Episode[]> {
    await this.ensureInitialized()
    
    const anime = this.animeCache.get(animeId)
    if (!anime) {
      throw new Error(`Anime not found: ${animeId}`)
    }
    
    return this.crawlerService.fetchEpisodes(anime.detailUrl)
  }

  /**
   * 搜索番剧
   */
  async search(keyword: string, page: number = 1): Promise<AnimePage> {
    await this.ensureInitialized()
    
    const allAnime = Array.from(this.animeCache.values())
    
    // 简繁转换（简单实现）
    const variants = this.getSearchVariants(keyword)
    
    // 过滤
    const filtered = allAnime.filter(anime => {
      const title = anime.title.toLowerCase()
      return variants.some(v => title.includes(v.toLowerCase()))
    })
    
    // 分页
    const pageSize = PAGINATION.DEFAULT_PAGE_SIZE
    const totalPages = Math.ceil(filtered.length / pageSize)
    const startIdx = (page - 1) * pageSize
    const endIdx = startIdx + pageSize
    
    return {
      animeList: filtered.slice(startIdx, endIdx),
      currentPage: page,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1
    }
  }

  /**
   * 获取搜索变体（简繁）
   */
  private getSearchVariants(keyword: string): string[] {
    const variants = new Set([keyword])
    
    // 简繁转换表（常用字）
    const traditionalMap: Record<string, string> = {
      '动': '動',
      '画': '畫',
      '梦': '夢',
      '门': '門',
      '见': '見',
      '贝': '貝',
      '长': '長',
      '风': '風',
      '龙': '龍'
    }
    
    // 生成繁体变体
    let traditional = keyword
    for (const [s, t] of Object.entries(traditionalMap)) {
      traditional = traditional.replace(new RegExp(s, 'g'), t)
    }
    if (traditional !== keyword) {
      variants.add(traditional)
    }
    
    return Array.from(variants)
  }

  /**
   * 获取缓存状态
   */
  getCacheStatus(): CacheStatus {
    const cachedCovers = this.databaseService.getCoverCacheCount()
    
    return {
      animeCount: this.animeCache.size,
      coversCached: cachedCovers,
      lastRefresh: null, // TODO: 记录最后刷新时间
      isRefreshing: this.isRefreshing,
      initialLoadComplete: this.cacheInitialized,
      progress: {
        currentPage: 0,
        totalPages: 0,
        currentIndex: 0,
        totalAnime: this.animeCache.size,
        isFetching: this.isRefreshing
      }
    }
  }

  /**
   * 刷新缓存
   */
  async refreshCache(): Promise<void> {
    if (this.isRefreshing) {
      log.warn('[AnimeService] Cache refresh already in progress')
      return
    }
    
    this.isRefreshing = true
    this.emit('refreshStart')
    
    try {
      log.info('[AnimeService] Refreshing cache...')
      
      // 重新加载列表
      await this.loadAnimeList()
      
      this.emit('refreshComplete')
      log.info('[AnimeService] Cache refreshed')
    } catch (error) {
      this.emit('refreshError', error)
      log.error('[AnimeService] Failed to refresh cache:', error)
      throw error
    } finally {
      this.isRefreshing = false
    }
  }

  /**
   * 确保已初始化
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.cacheInitialized) {
      await this.initialize()
    }
  }

  /**
   * 延迟
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 获取所有番剧（用于导出等）
   */
  getAllAnime(): Anime[] {
    return Array.from(this.animeCache.values())
  }

  /**
   * 关闭服务
   */
  close(): void {
    this.stopBackgroundRefresh()
    this.removeAllListeners()
    log.info('[AnimeService] Service closed')
  }
}
