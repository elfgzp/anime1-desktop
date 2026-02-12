/**
 * 番剧服务
 * 
 * 对应原项目: src/services/anime_cache_service.py
 * 职责: 番剧数据管理、缓存、搜索
 */

import type { DatabaseService } from '../database'
import type { CrawlerService } from '../crawler'
import type { Anime, AnimePage, Episode, CacheStatus, BangumiInfo } from '@shared/types'

export class AnimeService {
  private databaseService: DatabaseService
  private crawlerService: CrawlerService
  private animeCache: Map<string, Anime> = new Map()
  private cacheInitialized = false

  constructor(databaseService: DatabaseService, crawlerService: CrawlerService) {
    this.databaseService = databaseService
    this.crawlerService = crawlerService
  }

  async initialize(): Promise<void> {
    // 初始化缓存
    await this.loadAnimeList()
    this.cacheInitialized = true
  }

  private async loadAnimeList(): Promise<void> {
    // TODO: 从爬虫加载番剧列表
    // const animeList = await this.crawlerService.fetchAnimeList()
    // for (const anime of animeList) {
    //   this.animeCache.set(anime.id, anime)
    // }
  }

  async getList(page: number, pageSize: number): Promise<AnimePage> {
    // TODO: 实现分页逻辑
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

  async getDetail(animeId: string): Promise<Anime> {
    // TODO: 实现详情获取
    const anime = this.animeCache.get(animeId)
    if (!anime) {
      throw new Error('Anime not found')
    }
    return anime
  }

  async getEpisodes(animeId: string): Promise<Episode[]> {
    // TODO: 实现剧集获取
    const anime = this.animeCache.get(animeId)
    if (!anime) {
      throw new Error('Anime not found')
    }
    return this.crawlerService.fetchEpisodes(anime.detailUrl)
  }

  async search(keyword: string, page: number): Promise<AnimePage> {
    // TODO: 实现搜索逻辑（支持简繁转换）
    const allAnime = Array.from(this.animeCache.values())
    const filtered = allAnime.filter(a => 
      a.title.toLowerCase().includes(keyword.toLowerCase())
    )
    
    const pageSize = 24
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

  async getBangumiInfo(animeId: string): Promise<BangumiInfo | null> {
    // TODO: 实现 Bangumi 信息获取
    // 1. 先查缓存
    // 2. 缓存未命中则调用爬虫
    return null
  }

  async getCacheStatus(): Promise<CacheStatus> {
    return {
      animeCount: this.animeCache.size,
      coversCached: 0,
      lastRefresh: null,
      isRefreshing: false,
      initialLoadComplete: this.cacheInitialized,
      progress: {
        currentPage: 0,
        totalPages: 0,
        currentIndex: 0,
        totalAnime: 0,
        isFetching: false
      }
    }
  }

  async refreshCache(): Promise<void> {
    // TODO: 实现缓存刷新
    await this.loadAnimeList()
  }
}
