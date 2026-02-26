import { test, expect } from '../fixtures'

test('调试 preload', async ({ window }) => {
  // 检查 window.api 是否存在
  const info = await window.evaluate(() => {
    return {
      hasApi: typeof window.api !== 'undefined',
      apiKeys: typeof window.api !== 'undefined' ? Object.keys(window.api) : [],
      userAgent: navigator.userAgent,
    }
  })
  
  console.log('Window info:', info)
  
  // 列出所有全局变量
  const globals = await window.evaluate(() => {
    return Object.keys(window).filter(k => !k.startsWith('_'))
  })
  
  console.log('Global variables:', globals.slice(0, 20))
})
