/**
 * Playwright Electron 测试 Fixtures
 * 
 * 提供 Electron 应用测试的基础 fixture
 */
import { test as base, expect, type ElectronApplication, type Page } from '@playwright/test'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// 测试数据目录
const TEST_DATA_DIR = resolve(__dirname, '../../test-data/e2e')

// Electron Fixture 类型
type ElectronFixtures = {
  electronApp: ElectronApplication
  window: Page
  testData: {
    dir: string
    cleanup: () => Promise<void>
  }
}

/**
 * 检查是否有构建好的前端文件
 */
function hasFrontendBuild(): boolean {
  return existsSync(resolve(__dirname, '../../dist/index.html'))
}

/**
 * 扩展的 test fixture
 */
export const test = base.extend<ElectronFixtures>({
  // 每个测试都创建新的 Electron 应用实例
  electronApp: async ({}, use, testInfo) => {
    const { _electron: electron } = await import('@playwright/test')
    
    console.log(`[E2E] Launching Electron for test: ${testInfo.title}`)
    
    // 使用构建好的 main 进程文件
    const mainPath = resolve(__dirname, '../../dist-electron/main/index.js')
    
    console.log('[E2E] Main path:', mainPath)
    console.log('[E2E] Test data dir:', TEST_DATA_DIR)
    console.log('[E2E] Frontend build exists:', hasFrontendBuild())
    
    // 环境变量
    const env: Record<string, string> = {
      ...process.env as Record<string, string>,
      NODE_ENV: 'test',
      E2E_TEST: 'true',
      APP_DATA_DIR: TEST_DATA_DIR,
      DISABLE_UPDATE_CHECK: 'true',
    }
    
    // 如果有前端构建，使用生产模式
    if (hasFrontendBuild()) {
      console.log('[E2E] Using production mode with built frontend')
      env.NODE_ENV = 'production'
      env.VITE_DEV_SERVER_URL = ''  // 清空 dev server URL
    } else {
      console.log('[E2E] WARNING: No frontend build found, tests may fail if dev server is not running')
      console.log('[E2E] Run "npm run build" first for reliable tests')
    }
    
    const electronApp = await electron.launch({
      headless: true,
      args: [mainPath, '--no-sandbox', '--enable-logging', '--v=1'],
      cwd: resolve(__dirname, '../..'),
      env: {
        ...env,
        ELECTRON_ENABLE_LOGGING: 'true',
      },
      timeout: 60000,
    })

    // 监听控制台消息
    electronApp.on('console', (msg) => {
      const text = msg.text()
      // 只记录错误和警告，减少输出噪音
      if (msg.type() === 'error' || text.includes('error') || text.includes('Error')) {
        console.log(`[Electron Console] ${msg.type()}: ${text.substring(0, 200)}`)
      }
    })

    // 监听窗口创建
    electronApp.on('window', (page) => {
      console.log(`[E2E] Window created: ${page.url()}`)
    })

    await use(electronApp)

    console.log('[E2E] Closing Electron app...')
    // 清理：关闭应用
    await electronApp.close()
  },

  // 获取主窗口
  window: async ({ electronApp }, use) => {
    console.log('[E2E] Waiting for first window...')
    
    // 等待第一个窗口创建
    const window = await electronApp.firstWindow()
    
    console.log('[E2E] First window created, URL:', await window.url())
    
    // 等待应用加载完成
    try {
      await window.waitForLoadState('domcontentloaded', { timeout: 10000 })
      console.log('[E2E] DOM content loaded')
    } catch (e) {
      console.warn('[E2E] Timeout waiting for domcontentloaded')
    }
    
    // 等待网络空闲（如果适用）
    try {
      await window.waitForLoadState('networkidle', { timeout: 5000 })
      console.log('[E2E] Network idle')
    } catch {
      // 忽略超时
    }
    
    await use(window)
  },

  // 测试数据目录
  testData: async ({}, use) => {
    const fs = await import('fs/promises')
    
    // 确保测试数据目录存在
    await fs.mkdir(TEST_DATA_DIR, { recursive: true })
    
    const cleanup = async () => {
      try {
        await fs.rm(TEST_DATA_DIR, { recursive: true, force: true })
      } catch {
        // 忽略清理错误
      }
    }
    
    await use({ dir: TEST_DATA_DIR, cleanup })
  },
})

export { expect }

/**
 * 等待指定时间
 */
export async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 等待条件满足
 */
export async function waitFor<T>(
  fn: () => Promise<T> | T,
  options: { timeout?: number; interval?: number } = {}
): Promise<T> {
  const { timeout = 10000, interval = 100 } = options
  const startTime = Date.now()
  
  while (Date.now() - startTime < timeout) {
    try {
      const result = await fn()
      if (result) return result
    } catch {
      // 忽略错误，继续等待
    }
    await sleep(interval)
  }
  
  throw new Error(`waitFor timeout after ${timeout}ms`)
}
