import { test, expect } from '../fixtures'
import { resolve } from 'path'

test('测试简化版 preload', async ({ electronApp, window }) => {
  // 使用一个简化版的 preload 脚本
  const simplePreloadPath = '/tmp/test-preload-preload.js'
  
  // 通过 Electron 主进程创建一个测试窗口
  const result = await electronApp.evaluate(async ({ BrowserWindow }, preloadPath) => {
    const win = new BrowserWindow({
      width: 400,
      height: 300,
      show: false,
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        sandbox: false,
        nodeIntegration: false,
      }
    })
    
    await win.loadURL('data:text/html,<html><body><h1>Test</h1><script>console.log("Page loaded, window.api:", window.api)</script></body></html>')
    
    // 等待一下让 preload 执行
    await new Promise(r => setTimeout(r, 1000))
    
    // 检查 window.api
    const hasApi = await win.webContents.executeJavaScript('typeof window.api !== "undefined"')
    const apiKeys = await win.webContents.executeJavaScript('Object.keys(window.api || {})')
    
    win.close()
    
    return { hasApi, apiKeys }
  }, simplePreloadPath)
  
  console.log('Test preload result:', result)
  expect(result.hasApi).toBe(true)
  expect(result.apiKeys).toContain('ping')
})
