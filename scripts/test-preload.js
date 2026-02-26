#!/usr/bin/env node
/**
 * Preload 测试脚本
 * 使用 Playwright 连接真实的 Electron 窗口进行测试
 */

const { _electron: electron } = require('playwright-core')
const path = require('path')

async function testPreload() {
  console.log('[Test] Starting Electron...')
  
  const electronApp = await electron.launch({
    args: [path.join(__dirname, '../dist-electron/main/index.js')],
    env: {
      ...process.env,
      NODE_ENV: 'development'
    }
  })

  console.log('[Test] Electron started, waiting for window...')
  
  // 等待第一个窗口
  const window = await electronApp.firstWindow()
  
  // 等待页面加载
  await window.waitForLoadState('networkidle')
  await new Promise(r => setTimeout(r, 3000)) // 等待 3 秒确保 preload 执行

  console.log('[Test] Checking window.api...')
  
  // 检查 window.api 是否存在
  const hasApi = await window.evaluate(() => {
    return typeof window.api !== 'undefined'
  })
  
  console.log('[Test] window.api exists:', hasApi)
  
  if (hasApi) {
    // 检查 api 的具体方法
    const apiMethods = await window.evaluate(() => {
      return {
        hasWindow: typeof window.api?.window !== 'undefined',
        hasAnime: typeof window.api?.anime !== 'undefined',
        hasFavorite: typeof window.api?.favorite !== 'undefined',
        hasHistory: typeof window.api?.history !== 'undefined',
        hasSettings: typeof window.api?.settings !== 'undefined',
        hasDownload: typeof window.api?.download !== 'undefined',
        hasSystem: typeof window.api?.system !== 'undefined',
        hasUpdate: typeof window.api?.update !== 'undefined'
      }
    })
    
    console.log('[Test] API methods:', apiMethods)
    
    // 测试一个具体的 API 调用
    console.log('[Test] Testing window.api.anime.getList...')
    const result = await window.evaluate(async () => {
      try {
        const response = await window.api.anime.getList({ page: 1 })
        return { success: true, hasData: !!response.data }
      } catch (e) {
        return { success: false, error: e.message }
      }
    })
    
    console.log('[Test] API test result:', result)
    
    // 截图
    await window.screenshot({ path: path.join(__dirname, '../screenshots/test-preload.png') })
    console.log('[Test] Screenshot saved to screenshots/test-preload.png')
  } else {
    console.error('[Test] ❌ FAILED: window.api is undefined!')
    console.error('[Test] Preload script is not working correctly.')
  }

  await electronApp.close()
  console.log('[Test] Done.')
  process.exit(hasApi ? 0 : 1)
}

testPreload().catch(e => {
  console.error('[Test] Error:', e)
  process.exit(1)
})
