/**
 * 使用共享 Electron 实例的功能测试
 */
import { test, expect } from '../fixtures/shared'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

test.describe('共享实例 - 导航功能', () => {
  test('应该能够从首页导航到收藏页', async ({ window, resetState }) => {
    // 先重置状态
    await resetState()
    
    // 导航到收藏页
    await window.goto('file://' + resolve(__dirname, '../../dist/index.html') + '#/favorites')
    await window.waitForLoadState('domcontentloaded')
    
    // 验证 URL
    expect(window.url()).toContain('/favorites')
  })

  test('应该能够从首页导航到设置页', async ({ window, resetState }) => {
    await resetState()
    
    await window.goto('file://' + resolve(__dirname, '../../dist/index.html') + '#/settings')
    await window.waitForLoadState('domcontentloaded')
    
    expect(window.url()).toContain('/settings')
  })

  test('应该支持浏览器后退前进', async ({ window, resetState }) => {
    await resetState()
    
    // 访问两个页面
    const basePath = 'file://' + resolve(__dirname, '../../dist/index.html')
    await window.goto(basePath + '#/')
    await window.waitForLoadState('domcontentloaded')
    await window.waitForTimeout(500)
    
    await window.goto(basePath + '#/favorites')
    await window.waitForLoadState('domcontentloaded')
    await window.waitForTimeout(500)
    
    await window.goto(basePath + '#/settings')
    await window.waitForLoadState('domcontentloaded')
    await window.waitForTimeout(500)
    
    // 后退
    await window.goBack()
    await window.waitForTimeout(500)
    const url1 = window.url()
    expect(url1).toContain('/favorites')
    
    // 后退
    await window.goBack()
    await window.waitForTimeout(500)
    const url2 = window.url()
    expect(url2).not.toContain('/settings')
  })
})

test.describe('共享实例 - API 功能', () => {
  test('应该能够获取番剧列表', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 10 })
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })

  test('应该能够搜索番剧', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '火影', page: 1 })
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })

  test('应该能够获取收藏列表', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.favorite.getList()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(Array.isArray(result.data)).toBe(true)
  })

  test('应该能够添加和移除收藏', async ({ window, resetState }) => {
    await resetState()
    
    const testAnimeId = `test_${Date.now()}`
    
    // 添加收藏
    const addResult = await window.evaluate(async (id) => {
      return await window.api.favorite.add({
        animeId: id,
        title: 'Test Anime',
        detailUrl: 'https://example.com/test',
      })
    }, testAnimeId)
    
    expect(addResult.success).toBe(true)
    
    // 检查收藏状态
    const checkResult = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testAnimeId)
    
    expect(checkResult.data).toBe(true)
    
    // 移除收藏
    const removeResult = await window.evaluate(async (id) => {
      return await window.api.favorite.remove({ animeId: id })
    }, testAnimeId)
    
    expect(removeResult.success).toBe(true)
  })
})

test.describe('共享实例 - 设置功能', () => {
  test('应该能够获取所有设置', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })

  test('应该能够修改设置', async ({ window }) => {
    const testKey = 'test_setting'
    const testValue = 'test_value_' + Date.now()
    
    // 设置值
    const setResult = await window.evaluate(async ({ key, value }) => {
      return await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })
    
    expect(setResult.success).toBe(true)
    
    // 获取值验证
    const getResult = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(getResult.data).toBe(testValue)
  })
})

test.describe('共享实例 - 窗口控制', () => {
  test('应该能够获取窗口状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(result).toBeDefined()
    expect(typeof result.maximized).toBe('boolean')
    expect(typeof result.fullscreen).toBe('boolean')
  })
})
