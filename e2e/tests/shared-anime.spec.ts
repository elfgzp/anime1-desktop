/**
 * 番剧相关的共享实例测试
 */
import { test, expect } from '../fixtures/shared'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

test.describe('共享实例 - 番剧列表', () => {
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

test.describe('共享实例 - 番剧详情页', () => {
  test('应该能够导航到详情页', async ({ window, resetState }) => {
    await resetState()
    
    // 先获取列表
    const listResult = await window.evaluate(async () => {
      return await window.api.anime.getList({ page: 1, pageSize: 1 })
    })
    
    if (!listResult.success || !listResult.data?.list?.length) {
      test.skip('没有可用的番剧数据')
      return
    }
    
    const animeId = listResult.data.list[0].id
    
    // 导航到详情页
    const basePath = 'file://' + resolve(__dirname, '../../dist/index.html')
    await window.goto(`${basePath}#/anime/${animeId}`)
    await window.waitForLoadState('domcontentloaded')
    
    // 验证 URL
    expect(window.url()).toContain(`/anime/${animeId}`)
  })
})
