import { test, expect } from '../fixtures'

test('检查 preload 是否加载', async ({ electronApp, window }) => {
  // 监听 webContents 事件
  electronApp.on('window', async (page) => {
    console.log('[E2E] New window created:', page.url())
  })
  
  // 重新加载页面
  await window.reload()
  await window.waitForLoadState('domcontentloaded')
  
  // 等待一段时间确保 preload 执行
  await new Promise(r => setTimeout(r, 2000))
  
  // 检查 window 对象
  const check = await window.evaluate(() => {
    const keys = Object.keys(window)
    return {
      hasApi: 'api' in window,
      hasTestApi: 'testApi' in window,
      allKeys: keys.filter(k => !k.startsWith('_')).slice(0, 20)
    }
  })
  
  console.log('[E2E] Window check:', check)
  
  // 尝试在渲染进程中执行代码
  try {
    const result = await window.evaluate(() => {
      // 尝试访问可能的 API
      return {
        api: (window as any).api,
        typeofApi: typeof (window as any).api
      }
    })
    console.log('[E2E] API check result:', result)
  } catch (e: any) {
    console.log('[E2E] API check error:', e.message)
  }
})
