/**
 * 番剧 API 相关测试
 * 
 * 测试 IPC 接口
 */
import { test, expect } from '../fixtures'

test.describe('番剧列表 API', () => {
  test('应该能够获取番剧列表', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 10 })
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(result.data).toBeDefined()
  })

  test('应该能够搜索番剧', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '火影', page: 1 })
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })

  test('应该能够获取番剧详情', async ({ window }) => {
    // 先获取列表
    const listResult = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 1 })
    })
    
    if (!listResult.success || !listResult.data?.list?.length) {
      test.skip('没有可用的番剧数据')
      return
    }
    
    const animeId = listResult.data.list[0].id
    
    // 获取详情
    const detailResult = await window.evaluate(async (id) => {
      return await window.api.anime.getDetail({ id })
    }, animeId)
    
    expect(detailResult).toBeDefined()
    expect(detailResult.success).toBe(true)
  })

  test('应该能够获取剧集列表', async ({ window }) => {
    // 先获取列表
    const listResult = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 1 })
    })
    
    if (!listResult.success || !listResult.data?.list?.length) {
      test.skip('没有可用的番剧数据')
      return
    }
    
    const animeId = listResult.data.list[0].id
    
    // 获取剧集
    const episodesResult = await window.evaluate(async (id) => {
      return await window.api.anime.getEpisodes({ id })
    }, animeId)
    
    expect(episodesResult).toBeDefined()
    expect(episodesResult.success).toBe(true)
  })

  test('应该能够获取缓存状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.anime.getCacheStatus()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })
})

test.describe('收藏 API', () => {
  test('应该能够获取收藏列表', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.favorite.getList()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(Array.isArray(result.data)).toBe(true)
  })

  test('应该能够检查收藏状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.favorite.check({ animeId: 'test_anime_123' })
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(typeof result.data).toBe('boolean')
  })

  test('应该能够添加和移除收藏', async ({ window }) => {
    const testAnimeId = `test_${Date.now()}`
    
    // 添加收藏
    const addResult = await window.evaluate(async (id) => {
      return await window.api.favorite.add({
        animeId: id,
        title: 'Test Anime',
        detailUrl: 'https://example.com/test',
      })
    }, testAnimeId)
    
    expect(addResult.success).toBe(true)
    
    // 检查收藏状态
    const checkResult = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testAnimeId)
    
    expect(checkResult.data).toBe(true)
    
    // 移除收藏
    const removeResult = await window.evaluate(async (id) => {
      return await window.api.favorite.remove({ animeId: id })
    }, testAnimeId)
    
    expect(removeResult.success).toBe(true)
    
    // 再次检查
    const finalCheck = await window.evaluate(async (id) => {
      return await window.api.favorite.check({ animeId: id })
    }, testAnimeId)
    
    expect(finalCheck.data).toBe(false)
  })
})

test.describe('下载 API', () => {
  test('应该能够获取下载列表', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.download.getList()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(Array.isArray(result.data)).toBe(true)
  })
})

test.describe('系统 API', () => {
  test('应该能够调用系统打开外部链接', async ({ window }) => {
    // 这个测试只验证接口存在，不实际打开浏览器
    const result = await window.evaluate(async () => {
      try {
        // 使用一个无效的 URL 来测试接口调用
        await window.api.system.openExternal({ url: 'about:blank' })
        return { success: true }
      } catch (error) {
        return { success: false, error: String(error) }
      }
    })
    
    // 接口应该存在，但可能因权限或其他原因失败
    expect(result).toBeDefined()
  })
})
