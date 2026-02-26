/**
 * 共享 Electron 应用的测试 Fixtures
 * 
 * 多个测试共享同一个 Electron 实例，提高测试速度
 */
import { test as base, expect, type ElectronApplication, type Page } from '@playwright/test'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// 测试数据目录
const TEST_DATA_DIR = resolve(__dirname, '../../test-data/e2e')

// Electron Fixture 类型
type ElectronFixtures = {
  electronApp: ElectronApplication
  window: Page
  resetState: () => Promise<void>
}

/**
 * 扩展的 test fixture
 * 每个测试都启动一个 Electron 实例，但实例会被缓存重用
 */
export const test = base.extend<ElectronFixtures>({
  // Electron 应用 - test 级别
  electronApp: [async ({}, use) => {
    const { _electron: electron } = await import('@playwright/test')
    
    const mainPath = resolve(__dirname, '../../dist-electron/main/index.js')
    
    const electronApp = await electron.launch({
      args: [mainPath, '--no-sandbox'],
      cwd: resolve(__dirname, '../..'),
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
        APP_DATA_DIR: TEST_DATA_DIR,
        DISABLE_UPDATE_CHECK: 'true',
      },
      timeout: 60000,
    })

    await use(electronApp)

    await electronApp.close()
  }, { scope: 'test' }],

  // 窗口 - test 级别
  window: [async ({ electronApp }, use) => {
    const window = await electronApp.firstWindow()
    await window.waitForLoadState('domcontentloaded')
    await use(window)
  }, { scope: 'test' }],

  // 重置状态 - test 级别
  resetState: [async ({ window }, use) => {
    const reset = async () => {
      try {
        // 导航到首页
        const homePath = 'file://' + resolve(__dirname, '../../dist/index.html') + '#/'
        await window.goto(homePath)
        await window.waitForLoadState('domcontentloaded')
        
        // 清理 localStorage
        await window.evaluate(() => localStorage.clear()).catch(() => {})
        
        await window.waitForTimeout(300)
      } catch (error) {
        console.error('[E2E] State reset error:', error)
      }
    }
    
    await use(reset)
  }, { scope: 'test' }],
})

export { expect }

export async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
