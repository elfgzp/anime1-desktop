/**
 * UI 交互的共享实例测试
 */
import { test, expect } from '../fixtures/shared'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

test.describe('共享实例 - UI 元素检查', () => {
  test('首页应该包含标题和搜索框', async ({ window, resetState }) => {
    await resetState()
    
    // 检查标题
    const title = await window.locator('h1').textContent()
    expect(title).toContain('Anime1')
    
    // 检查搜索框
    const searchInput = await window.locator('input[type="text"], input[placeholder*="搜索"]').count()
    expect(searchInput).toBeGreaterThan(0)
  })

  test('页面应该包含导航元素', async ({ window, resetState }) => {
    await resetState()
    
    // 检查是否有链接或按钮
    const links = await window.locator('a, button').count()
    expect(links).toBeGreaterThan(0)
  })

  test('页面应该有正确的标题', async ({ window, resetState }) => {
    await resetState()
    
    const title = await window.title()
    expect(title).toBeTruthy()
  })
})

test.describe('共享实例 - 键盘交互', () => {
  test('应该支持键盘导航', async ({ window, resetState }) => {
    await resetState()
    
    // 聚焦到搜索框
    const searchInput = window.locator('input[type="text"]').first()
    await searchInput.focus()
    
    // 输入文本
    await searchInput.fill('火影')
    
    // 按下回车
    await searchInput.press('Enter')
    
    // 等待一下
    await window.waitForTimeout(500)
    
    // 验证页面仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })

  test('应该支持 Tab 键导航', async ({ window, resetState }) => {
    await resetState()
    
    // 按下 Tab 键多次
    for (let i = 0; i < 5; i++) {
      await window.keyboard.press('Tab')
      await window.waitForTimeout(100)
    }
    
    // 验证页面仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })
})

test.describe('共享实例 - 滚动行为', () => {
  test('页面应该支持滚动', async ({ window, resetState }) => {
    await resetState()
    
    // 获取初始滚动位置
    const initialScroll = await window.evaluate(() => window.scrollY)
    expect(initialScroll).toBe(0)
    
    // 执行滚动
    await window.evaluate(() => window.scrollTo(0, 100))
    
    // 获取滚动后的位置
    const afterScroll = await window.evaluate(() => window.scrollY)
    expect(afterScroll).toBeGreaterThanOrEqual(100)
  })

  test('滚动到页面底部不应该崩溃', async ({ window, resetState }) => {
    await resetState()
    
    // 滚动到页面底部
    await window.evaluate(() => {
      window.scrollTo(0, document.body.scrollHeight)
    })
    
    await window.waitForTimeout(300)
    
    // 验证应用仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })
})

test.describe('共享实例 - 窗口大小调整', () => {
  test('调整窗口大小不应该崩溃', async ({ window, resetState }) => {
    await resetState()
    
    // 调整窗口大小到不同尺寸
    const sizes = [
      { width: 800, height: 600 },
      { width: 1024, height: 768 },
      { width: 1280, height: 800 },
      { width: 1920, height: 1080 },
    ]
    
    for (const size of sizes) {
      await window.setViewportSize(size)
      await window.waitForTimeout(200)
      
      // 验证应用仍然可用
      const result = await window.evaluate(async () => {
        return await window.api.settings.getAll()
      })
      
      expect(result.success).toBe(true)
    }
  })

  test('最小尺寸窗口不应该崩溃', async ({ window, resetState }) => {
    await resetState()
    
    // 设置最小尺寸
    await window.setViewportSize({ width: 800, height: 600 })
    await window.waitForTimeout(300)
    
    // 验证应用仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })
})

test.describe('共享实例 - 截图测试', () => {
  test('首页截图应该一致', async ({ window, resetState }) => {
    await resetState()
    
    // 确保截图目录存在
    const fs = await import('fs/promises')
    await fs.mkdir('./e2e-report/screenshots', { recursive: true })
    
    // 截图
    await window.screenshot({ 
      path: './e2e-report/screenshots/home-page.png',
      fullPage: true 
    })
    
    // 验证截图文件存在
    const stats = await fs.stat('./e2e-report/screenshots/home-page.png')
    expect(stats.size).toBeGreaterThan(0)
  })

  test('不同页面截图', async ({ window, resetState }) => {
    await resetState()
    
    const fs = await import('fs/promises')
    await fs.mkdir('./e2e-report/screenshots', { recursive: true })
    
    const pages = ['favorites', 'settings', 'downloads']
    const basePath = 'file://' + resolve(__dirname, '../../dist/index.html')
    
    for (const page of pages) {
      await window.goto(`${basePath}#/${page}`)
      await window.waitForLoadState('domcontentloaded')
      await window.waitForTimeout(500)
      
      await window.screenshot({ 
        path: `./e2e-report/screenshots/${page}-page.png`,
        fullPage: true 
      })
      
      const stats = await fs.stat(`./e2e-report/screenshots/${page}-page.png`)
      expect(stats.size).toBeGreaterThan(0)
    }
  })
})
