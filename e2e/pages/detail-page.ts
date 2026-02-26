/**
 * 详情页面对象
 * 
 * 对应 views/Detail.vue
 */
import { BasePage } from './base-page'
import type { Page } from '@playwright/test'

export class DetailPage extends BasePage {
  readonly selectors = {
    title: '.detail-title',
    cover: '.detail-cover',
    description: '.detail-description',
    favoriteButton: '.favorite-btn',
    episodeList: '.episode-list',
    episodeItem: '.episode-item',
    playButton: '.play-btn',
    backButton: '.back-btn',
    bangumiInfo: '.bangumi-info',
  }

  constructor(page: Page) {
    super(page)
  }

  /**
   * 获取页面标题
   */
  async getTitle(): Promise<string> {
    return await this.getText(this.selectors.title)
  }

  /**
   * 获取描述
   */
  async getDescription(): Promise<string> {
    return await this.getText(this.selectors.description)
  }

  /**
   * 点击收藏/取消收藏按钮
   */
  async toggleFavorite(): Promise<void> {
    await this.safeClick(this.selectors.favoriteButton)
  }

  /**
   * 检查是否已收藏
   */
  async isFavorited(): Promise<boolean> {
    const btn = this.page.locator(this.selectors.favoriteButton)
    const text = await btn.textContent() || ''
    return text.includes('已收藏') || text.includes('取消收藏')
  }

  /**
   * 获取剧集列表
   */
  async getEpisodes(): Promise<Array<{ title: string; id: string }>> {
    const items = this.page.locator(this.selectors.episodeItem)
    const count = await items.count()
    const episodes = []
    
    for (let i = 0; i < count; i++) {
      const item = items.nth(i)
      const title = await item.textContent() || ''
      const id = await item.getAttribute('data-id') || ''
      episodes.push({ title: title.trim(), id })
    }
    
    return episodes
  }

  /**
   * 点击剧集播放
   */
  async clickEpisode(index: number): Promise<void> {
    await this.page.locator(this.selectors.episodeItem).nth(index).click()
  }

  /**
   * 点击返回按钮
   */
  async goBack(): Promise<void> {
    await this.safeClick(this.selectors.backButton)
  }

  /**
   * 获取 Bangumi 信息
   */
  async getBangumiInfo(): Promise<{ rating?: string; tags?: string[] }> {
    const info: { rating?: string; tags?: string[] } = {}
    
    const bangumiSection = this.page.locator(this.selectors.bangumiInfo)
    if (await bangumiSection.count() > 0) {
      info.rating = await bangumiSection.locator('.rating').textContent() || undefined
      const tagElements = bangumiSection.locator('.tag')
      const tagCount = await tagElements.count()
      info.tags = []
      for (let i = 0; i < tagCount; i++) {
        const tag = await tagElements.nth(i).textContent()
        if (tag) info.tags.push(tag.trim())
      }
    }
    
    return info
  }
}
