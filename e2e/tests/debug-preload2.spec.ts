import { test, expect } from '../fixtures'

test('检查 preload 路径', async ({ electronApp, window }) => {
  // 通过 Electron API 获取 webContents 信息
  const info = await electronApp.evaluate(async ({ BrowserWindow }) => {
    const win = BrowserWindow.getAllWindows()[0]
    if (!win) return { error: 'No window found' }
    
    const webContents = win.webContents
    return {
      preloadPath: (webContents as any).getWebPreferences()?.preload,
      url: webContents.getURL(),
    }
  })
  
  console.log('Electron webContents info:', info)
  
  // 检查页面加载的脚本
  const scripts = await window.evaluate(() => {
    return Array.from(document.querySelectorAll('script')).map(s => s.src)
  })
  
  console.log('Scripts in page:', scripts)
})
