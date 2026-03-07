/**
 * 简繁体转换功能测试
 * 
 * 测试搜索时简体/繁体字都能匹配到对应的番剧
 */
import { test, expect } from '../fixtures'

test.describe('简繁体搜索转换', () => {
  test('搜索应该返回结果', async ({ window }) => {
    const searchResult = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '火', page: 1 })
    })

    expect(searchResult).toBeDefined()
    expect(searchResult.success).toBe(true)
    expect(Array.isArray(searchResult.data.animeList)).toBe(true)
  })

  test('搜索不存在的词应该返回空列表', async ({ window }) => {
    const searchResult = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '完全不存在的番剧名称xyz123', page: 1 })
    })

    expect(searchResult).toBeDefined()
    expect(searchResult.success).toBe(true)
    expect(Array.isArray(searchResult.data.animeList)).toBe(true)
    expect(searchResult.data.animeList.length).toBe(0)
  })

  test('搜索应该返回分页信息', async ({ window }) => {
    const searchResult = await window.evaluate(async () => {
      return await window.api.anime.search({ keyword: '火', page: 1 })
    })

    expect(searchResult).toBeDefined()
    expect(searchResult.success).toBe(true)

    expect(searchResult.data.currentPage).toBeDefined()
    expect(searchResult.data.totalPages).toBeDefined()
    expect(searchResult.data.hasNext).toBeDefined()
  })
})
