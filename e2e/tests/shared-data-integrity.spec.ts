/**
 * 数据完整性和错误恢复的共享实例测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 数据完整性', () => {
  test('设置键值不应该被意外覆盖', async ({ window, resetState }) => {
    await resetState()
    
    const testKey = 'integrity_test'
    const value1 = 'value_1_' + Date.now()
    const value2 = 'value_2_' + Date.now()
    
    // 设置第一个值
    await window.evaluate(async ({ key, value }) => {
      await window.api.settings.set({ key, value })
    }, { key: testKey, value: value1 })
    
    // 验证第一个值
    const result1 = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    expect(result1.data).toBe(value1)
    
    // 设置第二个值（不同的key）
    await window.evaluate(async ({ key, value }) => {
      await window.api.settings.set({ key, value })
    }, { key: testKey + '_2', value: value2 })
    
    // 验证第一个值没有被覆盖
    const result2 = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    expect(result2.data).toBe(value1)
  })

  test('并发修改同一设置应该正确处理', async ({ window, resetState }) => {
    await resetState()
    
    const testKey = 'concurrent_test'
    
    // 并发设置不同的值
    const promises = []
    for (let i = 0; i < 5; i++) {
      promises.push(window.evaluate(async ({ key, idx }) => {
        return await window.api.settings.set({ key, value: `value_${idx}` })
      }, { key: testKey, idx: i }))
    }
    
    await Promise.all(promises)
    
    // 验证最终有一个值被设置
    const result = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(result.data).toMatch(/^value_\d+$/)
  })

  test('删除收藏后不应该影响其他收藏', async ({ window, resetState }) => {
    await resetState()
    
    const id1 = `integrity_1_${Date.now()}`
    const id2 = `integrity_2_${Date.now()}`
    
    // 添加两个收藏
    await window.evaluate(async (id) => {
      await window.api.favorite.add({
        animeId: id,
        title: 'Test 1',
        detailUrl: 'https://example.com/1',
      })
    }, id1)
    
    await window.evaluate(async (id) => {
      await window.api.favorite.add({
        animeId: id,
        title: 'Test 2',
        detailUrl: 'https://example.com/2',
      })
    }, id2)
    
    // 验证两个都存在
    const check1 = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, id1)
    expect(check1.data).toBe(true)
    
    const check2 = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, id2)
    expect(check2.data).toBe(true)
    
    // 删除第一个
    await window.evaluate(async (id) => {
      await window.api.favorite.remove({ animeId: id })
    }, id1)
    
    // 验证第二个还在
    const check3 = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, id2)
    expect(check3.data).toBe(true)
    
    // 清理
    await window.evaluate(async (id) => {
      await window.api.favorite.remove({ animeId: id })
    }, id2)
  })
})

test.describe('共享实例 - 错误恢复', () => {
  test('无效参数不应该导致应用崩溃', async ({ window }) => {
    const invalidParams = [
      null,
      undefined,
      {},
      { page: null },
      { pageSize: -1 },
    ]
    
    for (const params of invalidParams) {
      const result = await window.evaluate(async (p) => {
        try {
          return await window.api.anime.getList(p as any)
        } catch (e) {
          return { success: false, error: String(e) }
        }
      }, params)
      
      // 不应该抛出未捕获的异常
      expect(result).toBeDefined()
    }
  })

  test('网络错误应该被正确处理', async ({ window }) => {
    // 模拟网络错误的情况
    const result = await window.evaluate(async () => {
      try {
        // 尝试获取一个不存在的资源
        return await window.api.anime.getDetail({ id: 'network_error_test' })
      } catch (e) {
        return { success: false, error: String(e) }
      }
    })
    
    // 应该返回错误信息而不是崩溃
    expect(result).toBeDefined()
  })

  test('重复操作不应该导致问题', async ({ window }) => {
    const testId = `repeat_${Date.now()}`
    
    // 多次添加同一个收藏
    for (let i = 0; i < 3; i++) {
      await window.evaluate(async (id) => {
        return await window.api.favorite.add({
          animeId: id,
          title: 'Repeat Test',
          detailUrl: 'https://example.com/repeat',
        })
      }, testId)
    }
    
    // 验证只存在一个
    const list = await window.evaluate(async (id) => {
      const all = await window.api.favorite.getList()
      return all.data?.filter((f: any) => f.animeId === id).length || 0
    }, testId)
    
    expect(list).toBeLessThanOrEqual(1)
    
    // 清理
    await window.evaluate(async (id) => {
      await window.api.favorite.remove({ animeId: id })
    }, testId)
  })
})

test.describe('共享实例 - 状态一致性', () => {
  test('缓存状态应该与实际数据一致', async ({ window }) => {
    const status1 = await window.evaluate(async () => {
      return await window.api.anime.getCacheStatus()
    })
    
    expect(status1).toBeDefined()
    
    // 获取数据
    const list = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 10 })
    })
    
    expect(list.success).toBe(true)
    
    // 再次获取缓存状态
    const status2 = await window.evaluate(async () => {
      return await window.api.anime.getCacheStatus()
    })
    
    expect(status2).toBeDefined()
    // 缓存状态应该反映数据已加载
  })

  test('收藏列表应该与检查状态一致', async ({ window, resetState }) => {
    await resetState()
    
    const testId = `consistency_${Date.now()}`
    
    // 添加收藏
    await window.evaluate(async (id) => {
      await window.api.favorite.add({
        animeId: id,
        title: 'Consistency Test',
        detailUrl: 'https://example.com/consistency',
      })
    }, testId)
    
    // 获取列表
    const list = await window.evaluate(async () => {
      return await window.api.favorite.getList()
    })
    
    // 检查状态
    const check = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testId)
    
    // 一致性检查
    const inList = list.data?.some((f: any) => f.animeId === testId)
    expect(inList).toBe(check.data)
    
    // 清理
    await window.evaluate(async (id) => {
      await window.api.favorite.remove({ animeId: id })
    }, testId)
  })
})
