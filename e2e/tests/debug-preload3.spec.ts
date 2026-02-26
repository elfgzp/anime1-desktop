import { test, expect } from '../fixtures'

test('简单检查', async ({ electronApp, window }) => {
  // 尝试执行 IPC
  const result = await window.evaluate(async () => {
    try {
      // @ts-ignore
      if (window.api && window.api.settings) {
        // @ts-ignore
        return await window.api.settings.getAll()
      }
      return { error: 'window.api.settings not found' }
    } catch (e: any) {
      return { error: e.message }
    }
  })
  
  console.log('IPC result:', result)
  
  // 也检查 window 对象
  const windowInfo = await window.evaluate(() => {
    return {
      apiExists: 'api' in window,
      apiType: typeof (window as any).api,
      keys: Object.keys(window).slice(0, 10)
    }
  })
  
  console.log('Window info:', windowInfo)
})
