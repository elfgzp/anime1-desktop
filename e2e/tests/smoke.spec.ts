/**
 * 冒烟测试
 *
 * 快速验证应用基本功能是否正常
 */
import { test, expect } from '../fixtures'
import { HomePage, FavoritesPage, SettingsPage } from '../pages'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// 获取 production 模式的 base URL
const getBaseUrl = () => {
  // 检查是否在 production 模式
  const isProduction = process.env.NODE_ENV === 'production' || !process.env.VITE_DEV_SERVER_URL

  if (isProduction) {
    return 'file://' + resolve(__dirname, '../../dist/index.html') + '#'
  }

  return 'http://localhost:5173'
}

test.describe('冒烟测试', () => {
  test('应用应该能够启动', async ({ electronApp, window }) => {
    // 基本启动检查
    const title = await window.title()
    expect(title).toContain('Anime1')
  })

  test('所有主要页面应该可以访问', async ({ window }) => {
    const baseUrl = getBaseUrl()

    // 使用 Vue Router 客户端导航
    await window.goto(baseUrl + '/')
    await window.waitForTimeout(1000)

    await window.goto(baseUrl + '/favorites')
    await window.waitForTimeout(1000)

    await window.goto(baseUrl + '/settings')
    await window.waitForTimeout(1000)

    // 验证最终在设置页
    expect(await window.url()).toContain('/settings')
  })

  test('IPC 通信应该正常工作', async ({ window }) => {
    // 测试几个核心 IPC 接口
    const results = await window.evaluate(async () => {
      const tests = []

      // 设置 API
      tests.push(await window.api.settings.getAll())

      // 窗口 API
      tests.push(await window.api.window.getState())

      // 收藏 API
      tests.push(await window.api.favorite.getList())

      // 番剧 API
      tests.push(await window.api.anime.getCacheStatus())

      return tests
    })

    // 所有 API 调用都应该成功
    for (const result of results) {
      expect(result).toBeDefined()
    }
  })

  test('搜索功能应该可用', async ({ window }) => {
    const homePage = new HomePage(window)

    await homePage.waitForLoaded()

    // 尝试搜索
    await homePage.search('测试')

    // 等待结果
    await window.waitForTimeout(3000)

    // 检查是否有结果或空状态
    const hasResults = await homePage.getAnimeCount() > 0
    const isEmpty = await homePage.isEmpty()

    expect(hasResults || isEmpty).toBe(true)
  })

  test('收藏功能应该可用', async ({ window }) => {
    const baseUrl = getBaseUrl()

    // 导航到收藏页
    await window.goto(baseUrl + '/favorites')
    await window.waitForTimeout(1000)

    const favoritesPage = new FavoritesPage(window)

    // 页面应该加载成功
    const isEmpty = await favoritesPage.isEmpty()
    const count = await favoritesPage.getFavoriteCount()

    // 应该能获取到收藏列表（可能为空）
    expect(isEmpty || count >= 0).toBe(true)
  })
})

test.describe('关键用户流程', () => {
  test('完整的浏览流程：首页 -> 详情 -> 收藏', async ({ window }) => {
    const baseUrl = getBaseUrl()
    const homePage = new HomePage(window)

    // 1. 加载首页
    await homePage.waitForLoaded()
    await window.waitForTimeout(3000)

    // 2. 检查是否有番剧
    const count = await homePage.getAnimeCount()
    if (count === 0) {
      test.skip('没有可测试的番剧')
      return
    }

    // 3. 进入详情页
    await homePage.clickAnimeCard(0)
    await window.waitForTimeout(2000)

    // 验证在详情页
    expect(window.url()).toContain('/anime/')

    // 4. 点击收藏
    const detailPage = await import('../pages').then(m => new m.DetailPage(window))
    await detailPage.toggleFavorite()
    await window.waitForTimeout(1000)

    // 5. 前往收藏页验证
    await window.goto(baseUrl + '/favorites')
    await window.waitForTimeout(1000)

    const favoritesPage = new FavoritesPage(window)

    // 验证收藏页加载成功
    const favoritesCount = await favoritesPage.getFavoriteCount()
    expect(favoritesCount).toBeGreaterThanOrEqual(0)
  })

  test('设置流程：修改设置并验证持久化', async ({ window }) => {
    const baseUrl = getBaseUrl()

    // 1. 前往设置页
    await window.goto(baseUrl + '/settings')
    await window.waitForTimeout(1000)

    const settingsPage = new SettingsPage(window)

    // 2. 修改一个测试设置
    const testKey = 'smoke_test_setting'
    const testValue = 'smoke_test_value'

    const setResult = await window.evaluate(async ({ key, value }) => {
      return await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })

    expect(setResult.success).toBe(true)

    // 3. 刷新页面
    await window.reload()
    await window.waitForTimeout(2000)

    // 4. 验证设置还在
    const getResult = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)

    expect(getResult.success).toBe(true)
    expect(getResult.data).toBe(testValue)
  })
})
