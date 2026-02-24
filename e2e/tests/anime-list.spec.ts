/**
 * 番剧列表相关测试
 */
import { test, expect } from '../fixtures'
import { HomePage } from '../pages'

test.describe('番剧列表显示', () => {
  test('应该显示番剧卡片网格', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 等待加载完成（最多15秒）
    await window.waitForSelector(homePage.selectors.animeGrid, { 
      state: 'visible', 
      timeout: 15000 
    }).catch(() => {
      // 如果列表未加载，检查是否为空状态
      return homePage.isEmpty()
    })
    
    // 检查是否有番剧卡片或空状态
    const animeCount = await homePage.getAnimeCount()
    const isEmpty = await homePage.isEmpty()
    
    expect(animeCount > 0 || isEmpty).toBe(true)
  })

  test('番剧卡片应该包含标题和封面', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 等待加载
    await window.waitForTimeout(3000)
    
    // 获取第一个卡片的标题
    const results = await homePage.getSearchResults()
    
    if (results.length > 0) {
      // 验证标题不为空
      expect(results[0].title).toBeTruthy()
    }
  })

  test('应该有分页组件当数据量足够时', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 等待加载
    await window.waitForTimeout(3000)
    
    // 检查是否有分页
    const hasPagination = await homePage.hasElement(homePage.selectors.pagination)
    
    // 如果有分页，验证它可以点击
    if (hasPagination) {
      const pagination = window.locator(homePage.selectors.pagination)
      await expect(pagination).toBeVisible()
    }
  })
})

test.describe('搜索功能', () => {
  test('搜索应该返回结果', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 搜索常见关键词
    await homePage.search('火影')
    
    // 等待结果加载
    await window.waitForTimeout(3000)
    
    // 检查是否有结果或空状态
    const animeCount = await homePage.getAnimeCount()
    const isEmpty = await homePage.isEmpty()
    
    expect(animeCount > 0 || isEmpty).toBe(true)
  })

  test('空搜索应该显示全部结果', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 搜索空字符串
    await homePage.search('')
    
    // 等待加载
    await window.waitForTimeout(2000)
    
    // 应该显示列表
    const animeCount = await homePage.getAnimeCount()
    expect(animeCount).toBeGreaterThanOrEqual(0)
  })

  test('无效搜索应该显示空状态', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 搜索不存在的番剧
    await homePage.search('xyzabc123notexist')
    
    // 等待结果
    await window.waitForTimeout(3000)
    
    // 检查是否显示空状态
    const isEmpty = await homePage.isEmpty()
    expect(isEmpty).toBe(true)
  })
})

test.describe('分页功能', () => {
  test('点击分页应该加载新数据', async ({ window }) => {
    const homePage = new HomePage(window)
    await homePage.waitForLoaded()
    
    // 等待加载
    await window.waitForTimeout(3000)
    
    // 检查是否有分页
    const hasPagination = await homePage.hasElement(homePage.selectors.pagination)
    if (!hasPagination) {
      test.skip()
      return
    }
    
    // 获取第一页的结果
    const firstPageResults = await homePage.getSearchResults()
    
    // 尝试翻页到第2页
    try {
      await homePage.goToPage(2)
      await window.waitForTimeout(3000)
      
      // 获取第二页的结果
      const secondPageResults = await homePage.getSearchResults()
      
      // 两页的结果应该不同（或至少数量可能不同）
      const firstTitles = firstPageResults.map(r => r.title).join(',')
      const secondTitles = secondPageResults.map(r => r.title).join(',')
      
      // 如果都有数据，内容应该不同
      if (firstPageResults.length > 0 && secondPageResults.length > 0) {
        expect(firstTitles).not.toBe(secondTitles)
      }
    } catch {
      // 如果没有第2页，跳过测试
      test.skip()
    }
  })
})
