import { test, expect } from '../fixtures'

test('检查控制台错误', async ({ electronApp, window }) => {
  const errors: string[] = []
  
  // 监听控制台错误
  electronApp.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text())
    }
  })
  
  // 等待一下收集错误
  await new Promise(r => setTimeout(r, 2000))
  
  console.log('控制台错误:', errors)
  
  // 尝试检查 preload 是否加载
  const preloadInfo = await window.evaluate(() => {
    return {
      location: window.location.href,
      origin: window.location.origin,
      protocol: window.location.protocol,
    }
  })
  
  console.log('页面信息:', preloadInfo)
})
