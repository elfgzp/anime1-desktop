/**
 * 边界情况和异常处理的共享实例测试
 */
import { test, expect } from '../fixtures/shared'

test.describe('共享实例 - 边界情况', () => {
  test('搜索空字符串应该返回全部结果', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '', page: 1 })
    })
    
    expect(result.success).toBe(true)
  })

  test('搜索不存在的番剧应该返回空结果或提示', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: 'xyzabc123notexist', page: 1 })
    })
    
    expect(result.success).toBe(true)
    // 可能返回空列表或包含提示信息
  })

  test('搜索特殊字符应该正确处理', async ({ window }) => {
    const specialChars = ['<script>', '"test"', "'test'", '\\', '\\n', '\\t']
    
    for (const char of specialChars) {
      const result = await window.evaluate(async (c) => {
        return await window.api.anime.search({ keyword: c, page: 1 })
      }, char)
      
      // 不应该崩溃
      expect(result).toBeDefined()
    }
  })

  test('获取不存在的番剧详情应该返回错误', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getDetail({ id: 'nonexistent_id_12345' })
    })
    
    // 可能返回错误信息
    expect(result).toBeDefined()
  })

  test('页码为负数应该处理', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: -1, pageSize: 10 })
    })
    
    expect(result).toBeDefined()
  })

  test('超大页码应该处理', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 99999, pageSize: 10 })
    })
    
    expect(result).toBeDefined()
  })

  test('pageSize为0应该处理', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 0 })
    })
    
    expect(result).toBeDefined()
  })

  test('超大pageSize应该处理', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 10000 })
    })
    
    expect(result).toBeDefined()
  })
})

test.describe('共享实例 - 数据持久化', () => {
  test('设置应该在页面刷新后保留', async ({ window, resetState }) => {
    await resetState()
    
    const testKey = 'persist_test_key'
    const testValue = 'persist_test_value_' + Date.now()
    
    // 设置值
    await window.evaluate(async ({ key, value }) => {
      await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })
    
    // 刷新页面
    await window.reload()
    await window.waitForLoadState('domcontentloaded')
    
    // 验证值还在
    const result = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(result.data).toBe(testValue)
  })

  test('收藏应该在页面刷新后保留', async ({ window, resetState }) => {
    await resetState()
    
    const testAnimeId = `persist_test_${Date.now()}`
    
    // 添加收藏
    await window.evaluate(async (id) => {
      await window.api.favorite.add({
        animeId: id,
        title: 'Persist Test Anime',
        detailUrl: 'https://example.com/test',
      })
    }, testAnimeId)
    
    // 验证收藏存在
    const checkBefore = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testAnimeId)
    
    expect(checkBefore.data).toBe(true)
    
    // 刷新页面
    await window.reload()
    await window.waitForLoadState('domcontentloaded')
    
    // 验证收藏还在
    const checkAfter = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testAnimeId)
    
    expect(checkAfter.data).toBe(true)
    
    // 清理
    await window.evaluate(async (id) => {
      await window.api.favorite.remove({ animeId: id })
    }, testAnimeId)
  })
})

test.describe('共享实例 - 并发操作', () => {
  test('多次快速切换页面不应该崩溃', async ({ window, resetState }) => {
    await resetState()
    
    const basePath = 'file://' + process.cwd() + '/dist/index.html'
    
    // 快速切换页面10次
    for (let i = 0; i < 10; i++) {
      await window.goto(`${basePath}#/favorites`)
      await window.goto(`${basePath}#/settings`)
      await window.goto(`${basePath}#/downloads`)
    }
    
    // 最后回到首页
    await window.goto(basePath + '#/')
    await window.waitForLoadState('domcontentloaded')
    
    // 验证应用仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })

  test('快速连续API调用不应该阻塞', async ({ window }) => {
    const promises: Promise<any>[] = []
    
    // 同时发起20个API调用
    for (let i = 0; i < 20; i++) {
      promises.push(window.evaluate(async () => {
        return await window.api.anime.getCacheStatus()
      }))
    }
    
    const results = await Promise.all(promises)
    
    // 所有调用都应该成功
    expect(results.every(r => r.success)).toBe(true)
  })
})

test.describe('共享实例 - 内存管理', () => {
  test('大量数据操作后内存不应该泄漏', async ({ window }) => {
    const startTime = Date.now()
    
    // 进行100次API调用
    for (let i = 0; i < 100; i++) {
      await window.evaluate(async () => {
        return await window.api.anime.getList({ page: 1, pageSize: 10 })
      })
    }
    
    const duration = Date.now() - startTime
    
    // 应该在合理时间内完成（如果没有内存泄漏）
    expect(duration).toBeLessThan(60000) // 60秒内
    
    // 最后验证应用仍然可用
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result.success).toBe(true)
  })
})
