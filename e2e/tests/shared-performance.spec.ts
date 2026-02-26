/**
 * 性能相关的共享实例测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 性能测试', () => {
  test('API 调用应该在合理时间内完成', async ({ window, resetState }) => {
    await resetState()
    
    const start = Date.now()
    
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 10 })
    })
    
    const duration = Date.now() - start
    
    expect(result.success).toBe(true)
    expect(duration).toBeLessThan(15000) // 15秒内完成（考虑网络延迟）
  })

  test('连续 API 调用不应该阻塞', async ({ window }) => {
    const start = Date.now()
    
    // 并发调用多个 API
    const results = await window.evaluate(async () => {
      const calls = [
        window.api.anime.getCacheStatus(),
        window.api.favorite.getList(),
        window.api.settings.getAll(),
        window.api.download.getList(),
      ]
      return await Promise.all(calls)
    })
    
    const duration = Date.now() - start
    
    // 所有调用都应该成功
    expect(results.every(r => r.success)).toBe(true)
    // 并发调用应该在合理时间内完成
    expect(duration).toBeLessThan(5000) // 5秒内完成
  })

  test('页面加载应该在合理时间内完成', async ({ window, resetState }) => {
    await resetState()
    
    const start = Date.now()
    await window.waitForLoadState('networkidle', { timeout: 10000 })
    const duration = Date.now() - start
    
    console.log(`页面加载时间: ${duration}ms`)
    expect(duration).toBeLessThan(10000) // 10秒内完成
  })
})
