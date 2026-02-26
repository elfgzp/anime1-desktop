/**
 * 收藏页面对象
 * 
 * 对应 views/Favorites.vue
 */
import { BasePage } from './base-page'
import type { Page } from '@playwright/test'

export class FavoritesPage extends BasePage {
  readonly selectors = {
    title: 'h1',
    empty: '.el-empty',
    favoriteList: '.favorite-list',
    favoriteItem: '.favorite-item',
    removeButton: '.remove-btn',
    animeTitle: '.anime-title',
    lastWatched: '.last-watched',
  }

  constructor(page: Page) {
    super(page)
  }

  /**
   * 导航到收藏页
   */
  async goto(): Promise<void> {
    // 通过点击导航菜单或直接使用路由
    await this.page.goto('/favorites')
    await this.waitForLoaded()
  }

  /**
   * 获取收藏数量
   */
  async getFavoriteCount(): Promise<number> {
    return await this.page.locator(this.selectors.favoriteItem).count()
  }

  /**
   * 获取收藏列表
   */
  async getFavorites(): Promise<Array<{ title: string; lastWatched?: string }>> {
    const items = this.page.locator(this.selectors.favoriteItem)
    const count = await items.count()
    const favorites = []
    
    for (let i = 0; i < count; i++) {
      const item = items.nth(i)
      const title = await item.locator(this.selectors.animeTitle).textContent() || ''
      const lastWatched = await item.locator(this.selectors.lastWatched).textContent().catch(() => undefined)
      favorites.push({ title: title.trim(), lastWatched: lastWatched?.trim() })
    }
    
    return favorites
  }

  /**
   * 移除收藏
   */
  async removeFavorite(index: number): Promise<void> {
    const item = this.page.locator(this.selectors.favoriteItem).nth(index)
    await item.locator(this.selectors.removeButton).click()
    // 等待确认对话框并确认
    await this.page.locator('.el-message-box__btns .el-button--primary').click()
  }

  /**
   * 点击收藏项进入详情
   */
  async clickFavorite(index: number): Promise<void> {
    await this.page.locator(this.selectors.favoriteItem).nth(index).click()
  }

  /**
   * 检查是否为空
   */
  async isEmpty(): Promise<boolean> {
    return await this.hasElement(this.selectors.empty)
  }
}
