import { test, expect } from '../fixtures'

test('捕获所有控制台消息', async ({ electronApp, window }) => {
  const messages: {type: string, text: string}[] = []
  
  // 监听所有控制台消息
  electronApp.on('console', (msg) => {
    messages.push({ type: msg.type(), text: msg.text() })
  })
  
  // 重新加载页面以捕获 preload 的日志
  await window.reload()
  await window.waitForLoadState('domcontentloaded')
  await new Promise(r => setTimeout(r, 2000))
  
  console.log('所有控制台消息:')
  messages.forEach(m => console.log(`[${m.type}] ${m.text.substring(0, 100)}`))
  
  // 检查 window.api
  const hasApi = await window.evaluate(() => 'api' in window)
  console.log('window.api exists:', hasApi)
})
