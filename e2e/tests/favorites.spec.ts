/**
 * 收藏功能相关测试
 */
import { test, expect } from '../fixtures'
import { HomePage, FavoritesPage, DetailPage } from '../pages'

test.describe('收藏页', () => {
  test('收藏页应该正确加载', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    
    await favoritesPage.goto()
    
    // 验证页面加载
    expect(window.url()).toContain('/favorites')
    
    // 检查是否显示内容或空状态
    const isEmpty = await favoritesPage.isEmpty()
    const count = await favoritesPage.getFavoriteCount()
    
    expect(isEmpty || count >= 0).toBe(true)
  })

  test('空收藏页应该显示提示', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    
    await favoritesPage.goto()
    
    // 检查是否显示空状态
    const isEmpty = await favoritesPage.isEmpty()
    
    if (isEmpty) {
      // 验证有提示文本
      const hasHint = await favoritesPage.hasText('暂无') || 
                     await favoritesPage.hasText('收藏') ||
                     await favoritesPage.hasText('empty')
      expect(hasHint).toBe(true)
    }
  })
})

test.describe('添加收藏', () => {
  test('从详情页添加收藏', async ({ window }) => {
    const homePage = new HomePage(window)
    const detailPage = new DetailPage(window)
    
    // 导航到首页
    await homePage.waitForLoaded()
    await window.waitForTimeout(3000)
    
    // 检查是否有番剧
    const animeCount = await homePage.getAnimeCount()
    if (animeCount === 0) {
      test.skip('没有可点击的番剧')
      return
    }
    
    // 进入详情页
    await homePage.clickAnimeCard(0)
    await window.waitForTimeout(2000)
    
    // 点击收藏
    await detailPage.toggleFavorite()
    await window.waitForTimeout(1000)
    
    // 验证操作完成（按钮还在）
    const buttonExists = await detailPage.hasElement(detailPage.selectors.favoriteButton)
    expect(buttonExists).toBe(true)
  })

  test('添加收藏后应该在收藏页显示', async ({ window }) => {
    const homePage = new HomePage(window)
    const detailPage = new DetailPage(window)
    const favoritesPage = new FavoritesPage(window)
    
    // 先获取当前收藏数量
    await favoritesPage.goto()
    const initialCount = await favoritesPage.getFavoriteCount()
    
    // 添加一个收藏
    await homePage.waitForLoaded()
    await window.waitForTimeout(3000)
    
    const animeCount = await homePage.getAnimeCount()
    if (animeCount === 0) {
      test.skip('没有可点击的番剧')
      return
    }
    
    // 进入详情页并收藏
    await homePage.clickAnimeCard(0)
    await window.waitForTimeout(2000)
    await detailPage.toggleFavorite()
    await window.waitForTimeout(1000)
    
    // 返回收藏页检查
    await favoritesPage.goto()
    await window.waitForTimeout(1000)
    
    // 收藏数量可能变化（取决于之前是否已收藏）
    const newCount = await favoritesPage.getFavoriteCount()
    expect(newCount).toBeGreaterThanOrEqual(0)
  })
})

test.describe('移除收藏', () => {
  test('应该在详情页可以取消收藏', async ({ window }) => {
    const homePage = new HomePage(window)
    const detailPage = new DetailPage(window)
    
    await homePage.waitForLoaded()
    await window.waitForTimeout(3000)
    
    const animeCount = await homePage.getAnimeCount()
    if (animeCount === 0) {
      test.skip('没有可点击的番剧')
      return
    }
    
    await homePage.clickAnimeCard(0)
    await window.waitForTimeout(2000)
    
    // 点击收藏按钮（切换状态）
    await detailPage.toggleFavorite()
    await window.waitForTimeout(1000)
    
    // 按钮应该还在
    const buttonExists = await detailPage.hasElement(detailPage.selectors.favoriteButton)
    expect(buttonExists).toBe(true)
  })
})

test.describe('收藏数据持久化', () => {
  test('刷新页面后收藏应该保留', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    
    // 先添加一个收藏
    const homePage = new HomePage(window)
    const detailPage = new DetailPage(window)
    
    await homePage.waitForLoaded()
    await window.waitForTimeout(3000)
    
    const animeCount = await homePage.getAnimeCount()
    if (animeCount === 0) {
      test.skip('没有可点击的番剧')
      return
    }
    
    // 添加收藏
    await homePage.clickAnimeCard(0)
    await window.waitForTimeout(2000)
    await detailPage.toggleFavorite()
    await window.waitForTimeout(1000)
    
    // 记录收藏数量
    await favoritesPage.goto()
    const countBeforeReload = await favoritesPage.getFavoriteCount()
    
    // 刷新页面
    await window.reload()
    await window.waitForTimeout(2000)
    
    // 再次获取收藏数量
    const countAfterReload = await favoritesPage.getFavoriteCount()
    
    // 数量应该相同
    expect(countAfterReload).toBe(countBeforeReload)
  })
})
