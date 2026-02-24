/**
 * 应用启动和窗口相关测试
 */
import { test, expect } from '../fixtures'
import { HomePage } from '../pages'

test.describe('应用启动', () => {
  test('应用应该正确启动并显示主窗口', async ({ electronApp, window }) => {
    // 验证窗口存在且可见
    expect(await window.isVisible()).toBe(true)
    
    // 验证窗口标题
    const title = await window.title()
    expect(title).toContain('Anime1')
  })

  test('窗口应该有正确的初始尺寸', async ({ window }) => {
    const size = await window.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }))
    
    // 最小尺寸检查
    expect(size.width).toBeGreaterThanOrEqual(800)
    expect(size.height).toBeGreaterThanOrEqual(600)
  })

  test('应用应该只创建一个窗口', async ({ electronApp }) => {
    const windows = await electronApp.windows()
    expect(windows.length).toBe(1)
  })
})

test.describe('应用加载', () => {
  test('首页应该正确加载', async ({ window }) => {
    const homePage = new HomePage(window)
    
    // 等待页面加载
    await homePage.waitForLoaded()
    
    // 验证页面标题
    const title = await homePage.getTitle()
    expect(title).toBe('Anime1 Desktop')
  })

  test('首页应该显示番剧列表或加载状态', async ({ window }) => {
    const homePage = new HomePage(window)
    
    // 等待加载完成
    await homePage.waitForLoaded()
    
    // 检查是否显示番剧列表或加载状态或空状态
    const hasAnimeList = await homePage.getAnimeCount() > 0
    const isLoading = await homePage.isLoading()
    const isEmpty = await homePage.isEmpty()
    
    // 至少满足其中一个条件
    expect(hasAnimeList || isLoading || isEmpty).toBe(true)
  })

  test('搜索框应该可用', async ({ window }) => {
    const homePage = new HomePage(window)
    
    // 检查搜索输入框是否存在
    const hasSearchInput = await homePage.hasElement(homePage.selectors.searchInput)
    expect(hasSearchInput).toBe(true)
  })
})

test.describe('IPC 通信', () => {
  test('应该能够通过 IPC 调用获取设置', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(result.data).toBeDefined()
  })

  test('应该能够通过 IPC 获取窗口状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(result).toBeDefined()
    expect(result.maximized).toBeDefined()
    expect(result.minimized).toBeDefined()
    expect(result.fullscreen).toBeDefined()
    expect(result.focused).toBeDefined()
  })
})
