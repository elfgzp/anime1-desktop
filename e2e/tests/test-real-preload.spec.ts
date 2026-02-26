import { test, expect } from '../fixtures'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

test('测试实际项目的 preload', async ({ electronApp }) => {
  // 先找到正确的 preload 路径
  const correctPath = resolve(__dirname, '../../dist-electron/preload/index.cjs')
  console.log('Correct preload path:', correctPath)
  
  // 通过 Electron 主进程创建一个测试窗口
  const result = await electronApp.evaluate(async ({ BrowserWindow }, preloadPath) => {
    console.log('[Main] Creating window with preload:', preloadPath)
    
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
    
    // 捕获控制台消息
    const logs: string[] = []
    win.webContents.on('console-message', (e, level, message) => {
      logs.push(`[${level}] ${message}`)
      console.log('[Renderer]', message)
    })
    
    await win.loadURL('data:text/html,<html><body><h1>Test Real Preload</h1></body></html>')
    
    // 等待一下让 preload 执行
    await new Promise(r => setTimeout(r, 2000))
    
    // 检查 window.api
    const hasApi = await win.webContents.executeJavaScript('typeof window.api !== "undefined"')
    const apiKeys = await win.webContents.executeJavaScript('Object.keys(window.api || {})')
    
    win.close()
    
    return { hasApi, apiKeys, logs, preloadPath }
  }, correctPath)
  
  console.log('Real preload result:', result)
  
  if (!result.hasApi) {
    console.log('Console logs:', result.logs)
  } else {
    console.log('API keys:', result.apiKeys)
  }
  
  expect(result.hasApi).toBe(true)
})
