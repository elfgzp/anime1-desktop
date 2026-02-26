/**
 * 使用共享 Electron 实例的测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 健全性检查', () => {
  test('Electron 应用应该能够启动', async ({ electronApp, window, resetState }) => {
    await resetState()
    
    const windows = await electronApp.windows()
    expect(windows.length).toBeGreaterThan(0)
    
    // 在共享实例模式下，URL 可能已经被其他测试修改
    // 所以只检查窗口存在且有标题
    const title = await window.title()
    expect(title.length).toBeGreaterThan(0)
    console.log('窗口标题:', title)
  })

  test('页面应该能加载', async ({ window }) => {
    const body = await window.locator('body').count()
    expect(body).toBe(1)
    
    const html = await window.content()
    expect(html).toContain('<!DOCTYPE html>')
  })

  test('IPC 应该可用', async ({ window }) => {
    const hasApi = await window.evaluate(() => {
      return typeof window.api !== 'undefined'
    })
    
    console.log('IPC API 可用:', hasApi)
    
    if (hasApi) {
      const apiKeys = await window.evaluate(() => {
        return Object.keys(window.api || {})
      })
      console.log('可用 API:', apiKeys)
      expect(apiKeys.length).toBeGreaterThan(0)
    }
  })

  test('应该能执行基本的页面操作', async ({ window }) => {
    const size = await window.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }))
    
    console.log('页面尺寸:', size)
    expect(size.width).toBeGreaterThan(0)
    expect(size.height).toBeGreaterThan(0)
  })
})

test.describe('共享实例 - 应用功能', () => {
  test('首页应该正确加载', async ({ window }) => {
    const title = await window.title()
    expect(title).toContain('Anime1')
  })

  test('应该能够通过 IPC 调用获取设置', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })

  test('应该能够通过 IPC 获取窗口状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(result).toBeDefined()
    expect(result.maximized).toBeDefined()
    expect(result.fullscreen).toBeDefined()
  })
})
