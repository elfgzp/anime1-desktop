/**
 * 下载相关的共享实例测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 下载功能', () => {
  test('应该能够获取下载列表', async ({ window, resetState }) => {
    await resetState()
    
    const result = await window.evaluate(async () => {
      return await window.api.download.getList()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(Array.isArray(result.data)).toBe(true)
  })
})

test.describe('共享实例 - 下载历史', () => {
  test('下载列表初始为空或包含历史记录', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.download.getList()
    })
    
    expect(result.success).toBe(true)
    // 可以是空数组或包含历史记录
    expect(Array.isArray(result.data)).toBe(true)
  })
})
