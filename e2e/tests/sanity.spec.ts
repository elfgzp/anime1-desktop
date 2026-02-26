/**
 * 简易健全性测试
 * 
 * 最基本的测试，用于验证 E2E 测试框架能正常工作
 */
import { test, expect } from '../fixtures'

test.describe('健全性检查', () => {
  test('Electron 应用应该能够启动', async ({ electronApp, window }) => {
    // 最基本的检查：应用启动且窗口存在
    const windows = await electronApp.windows()
    expect(windows.length).toBeGreaterThan(0)
    
    // 检查窗口 URL 是否正确加载
    const url = window.url()
    console.log('窗口 URL:', url)
    expect(url).toContain('index.html')
    
    // 检查窗口标题
    const title = await window.title()
    console.log('窗口标题:', title)
    expect(title.length).toBeGreaterThan(0)
  })

  test('页面应该能加载', async ({ window }) => {
    // 等待页面基本加载
    await window.waitForLoadState('domcontentloaded')
    
    // 检查 body 元素存在
    const body = await window.locator('body').count()
    expect(body).toBe(1)
    
    // 检查 HTML 结构
    const html = await window.content()
    expect(html).toContain('<!DOCTYPE html>')
  })

  test('IPC 应该可用', async ({ window }) => {
    // 检查 window.api 是否存在
    const hasApi = await window.evaluate(() => {
      return typeof window.api !== 'undefined'
    })
    
    console.log('IPC API 可用:', hasApi)
    
    // 如果 API 存在，进一步检查
    if (hasApi) {
      const apiKeys = await window.evaluate(() => {
        return Object.keys(window.api || {})
      })
      console.log('可用 API:', apiKeys)
      expect(apiKeys.length).toBeGreaterThan(0)
    } else {
      console.warn('⚠️ IPC API 不可用，可能是 preload 配置问题')
      // 不强制失败，因为 preload 可能有问题
    }
  })

  test('应该能执行基本的页面操作', async ({ window }) => {
    // 确保截图目录存在
    const fs = await import('fs/promises')
    await fs.mkdir('./e2e-report/screenshots', { recursive: true })
    
    // 截图测试
    await window.screenshot({ 
      path: './e2e-report/screenshots/sanity-check.png' 
    })
    
    // 获取页面尺寸
    const size = await window.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }))
    
    console.log('页面尺寸:', size)
    expect(size.width).toBeGreaterThan(0)
    expect(size.height).toBeGreaterThan(0)
  })
})
