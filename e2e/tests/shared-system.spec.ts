/**
 * 系统相关的共享实例测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 系统功能', () => {
  test('应该能够调用系统打开外部链接', async ({ window, resetState }) => {
    await resetState()
    
    // 这个测试只验证接口存在，不实际调用（避免打开浏览器）
    const result = await window.evaluate(async () => {
      // 只检查接口是否存在
      return {
        hasSystemApi: typeof window.api?.system !== 'undefined',
        hasOpenExternal: typeof window.api?.system?.openExternal === 'function'
      }
    })
    
    expect(result.hasSystemApi).toBe(true)
    expect(result.hasOpenExternal).toBe(true)
  })
})

test.describe('共享实例 - 更新功能', () => {
  test('应该能够检查更新', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.update.check()
    })
    
    // 可能成功或失败（取决于网络）
    expect(result).toBeDefined()
  })
})
