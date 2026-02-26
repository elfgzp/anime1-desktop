/**
 * 导航和路由相关测试
 */
import { test, expect } from '../fixtures'
import { HomePage, FavoritesPage, SettingsPage, DownloadsPage } from '../pages'

test.describe('页面导航', () => {
  test('应该能够从首页导航到收藏页', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    
    await favoritesPage.goto()
    
    // 验证 URL
    expect(window.url()).toContain('/favorites')
  })

  test('应该能够从首页导航到设置页', async ({ window }) => {
    const settingsPage = new SettingsPage(window)
    
    await settingsPage.goto()
    
    // 验证 URL
    expect(window.url()).toContain('/settings')
  })

  test('应该能够从首页导航到下载页', async ({ window }) => {
    const downloadsPage = new DownloadsPage(window)
    
    await downloadsPage.goto()
    
    // 验证 URL
    expect(window.url()).toContain('/downloads')
  })

  test('应该能够从其他页面返回首页', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    const homePage = new HomePage(window)
    
    // 先导航到收藏页
    await favoritesPage.goto()
    expect(window.url()).toContain('/favorites')
    
    // 返回首页
    await homePage.goto()
    expect(window.url()).not.toContain('/favorites')
  })
})

test.describe('浏览器导航', () => {
  test('应该支持浏览器后退前进', async ({ window }) => {
    const homePage = new HomePage(window)
    const favoritesPage = new FavoritesPage(window)
    const settingsPage = new SettingsPage(window)
    
    // 按顺序访问页面
    await homePage.goto()
    await favoritesPage.goto()
    await settingsPage.goto()
    
    // 后退
    await window.goBack()
    expect(window.url()).toContain('/favorites')
    
    // 后退
    await window.goBack()
    expect(window.url()).not.toContain('/favorites')
    expect(window.url()).not.toContain('/settings')
    
    // 前进
    await window.goForward()
    expect(window.url()).toContain('/favorites')
  })
})

test.describe('页面标题', () => {
  test('首页应该有正确的标题', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.goto()
    
    const title = await homePage.getTitle()
    expect(title).toBe('Anime1 Desktop')
  })

  test('收藏页应该显示收藏相关的内容', async ({ window }) => {
    const favoritesPage = new FavoritesPage(window)
    await favoritesPage.goto()
    
    // 等待页面加载
    await favoritesPage.waitForLoaded()
    
    // 检查是否有标题或空状态提示
    const hasTitle = await favoritesPage.hasText('收藏')
    const isEmpty = await favoritesPage.isEmpty()
    
    expect(hasTitle || isEmpty).toBe(true)
  })
})
