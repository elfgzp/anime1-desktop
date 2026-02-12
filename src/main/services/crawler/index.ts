/**
 * 爬虫服务
 * 
 * 对应原项目: src/parser/anime1_parser.py, src/parser/cover_finder.py
 * 整合 Anime1 和 Bangumi 爬虫
 */

import type { Anime, Episode, BangumiInfo } from '@shared/types'
import { Anime1Crawler } from './anime1'
import { BangumiCrawler } from './bangumi'

export * from './anime1'
export * from './bangumi'
export * from './http-client'

export class CrawlerService {
  private anime1: Anime1Crawler
  private bangumi: BangumiCrawler

  constructor() {
    this.anime1 = new Anime1Crawler()
    this.bangumi = new BangumiCrawler()
  }

  /**
   * 获取 Anime1 番剧列表
   */
  async fetchAnimeList(): Promise<Anime[]> {
    return this.anime1.fetchAnimeList()
  }

  /**
   * 获取番剧详情（年份、季节、字幕组）
   */
  async fetchAnimeDetail(url: string): Promise<{
    year: string
    season: string
    subtitleGroup: string
  }> {
    return this.anime1.fetchAnimeDetail(url)
  }

  /**
   * 获取剧集列表
   */
  async fetchEpisodes(detailUrl: string): Promise<Episode[]> {
    return this.anime1.fetchEpisodes(detailUrl)
  }

  /**
   * 查找 Bangumi 信息
   */
  async findBangumiInfo(
    title: string,
    year?: string,
    season?: string
  ): Promise<{ info: BangumiInfo; score: number } | null> {
    return this.bangumi.findBestMatch(title, year, season)
  }

  /**
   * 关闭所有爬虫
   */
  close(): void {
    this.anime1.close()
    this.bangumi.close()
  }
}
