/**
 * @integration
 * Bangumi 封面匹配优化测试
 * 
 * 测试那些曾经匹配错误的案例，确保修复后能够正确匹配
 * 
 * 运行: npx vitest run tests/integration/bangumi.cover.match.test.ts
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'

// 错误匹配案例（来自真实数据库）
const WRONG_MATCH_CASES = [
  {
    id: '1742',
    title: '娑婆氣',
    expectedCoverId: '340164_88L2x',
    description: '不应该匹配到戏剧性谋杀（100557）'
  },
  {
    id: '206081',
    title: '罪惡之淵',
    expectedCoverId: '54705_g0zBb',
    description: '不应该匹配到罪恶王冠（18635）'
  },
  {
    id: '1811',
    title: '和機器人啪啪啪能算在經驗人數裡嗎？？',
    expectedCoverId: '173020_RA7zG',
    description: '不应该匹配到爱、死亡 & 机器人（274613）'
  }
]

// 繁简不同ID的案例（这些是预期会不匹配的，但应该返回正确的动画）
const VARIANT_CASES = [
  {
    id: '1797',
    title: '靠死亡遊戲混飯吃。',
    expectedCoverId: '510753_3zw53',  // 繁体ID
    simplifiedId: '510753_8CZ48',     // 简体ID（Bangumi返回的）
    description: '繁简ID不同但都是正确结果'
  },
  {
    id: '1754',
    title: '小手指同學，請別亂摸',
    expectedCoverId: '592283_HZp8Q',
    simplifiedId: '541547_VC8lh',
    description: '繁简ID不同但都是正确结果'
  }
]

// 复杂标题案例
const COMPLEX_TITLE_CASES = [
  {
    id: '1813',
    title: '轉生之後的我變成了龍蛋～目標是世界最強～',
    expectedCoverId: '544106_S3Ua7',
    description: '长标题应该正确匹配'
  },
  {
    id: '1787',
    title: '花樣少年少女',
    expectedCoverId: '494564',
    description: '不应该匹配到单字"花"（579466）'
  },
  {
    id: 'test_rezero',
    title: 'Re:從零開始的異世界生活 第三季',
    expectedKeywords: ['Re:', '从零开始', '异世界'],
    description: 'Re:前缀应该被正确处理'
  }
]

describe('Bangumi 封面匹配优化', () => {
  let crawler: BangumiCrawler

  beforeAll(() => {
    crawler = new BangumiCrawler()
  })

  afterAll(() => {
    crawler.close()
  })

  describe('错误匹配修复', () => {
    it.each(WRONG_MATCH_CASES)(
      '[$id] $title - $description',
      async ({ title, expectedCoverId }) => {
        const result = await crawler.findBestMatch(title)
        
        expect(result).not.toBeNull()
        expect(result!.info.coverUrl).toBeDefined()
        
        // 提取封面ID
        const coverId = result!.info.coverUrl!.match(/(\d+_[^.]+)/)?.[1]
        
        // 不应该匹配到完全错误的动画
        // 注意：由于Bangumi可能有多个条目，我们只检查匹配到的不是已知的错误结果
        const wrongIds = ['100557', '18635', '274613']
        const matchedSubjectId = coverId?.split('_')[0]
        
        expect(
          wrongIds.includes(matchedSubjectId || ''),
          `错误匹配: 匹配到了 ${result!.info.title} (${coverId})`
        ).toBe(false)
        
        // 分数应该合理（至少有一定置信度）
        expect(result!.score).toBeGreaterThanOrEqual(30)
      },
      30000
    )
  })

  describe('繁简变体处理', () => {
    it.each(VARIANT_CASES)(
      '[$id] $title - $description',
      async ({ title, expectedCoverId, simplifiedId }) => {
        const result = await crawler.findBestMatch(title)
        
        expect(result).not.toBeNull()
        expect(result!.info.coverUrl).toBeDefined()
        
        const coverId = result!.info.coverUrl!.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        // 繁简ID应该对应同一个动画（ID前缀相同）
        const expectedSubjectId = expectedCoverId.split('_')[0]
        const simplifiedSubjectId = simplifiedId.split('_')[0]
        
        // 允许匹配到繁体或简体ID
        const isValidMatch = subjectId === expectedSubjectId || subjectId === simplifiedSubjectId
        
        expect(
          isValidMatch,
          `期望匹配 ${expectedCoverId} 或 ${simplifiedId}, 但匹配到了 ${coverId}`
        ).toBe(true)
      },
      30000
    )
  })

  describe('复杂标题处理', () => {
    it.each(COMPLEX_TITLE_CASES)(
      '[$id] $title - $description',
      async ({ title, expectedCoverId, expectedKeywords }) => {
        const result = await crawler.findBestMatch(title)
        
        expect(result).not.toBeNull()
        expect(result!.info.coverUrl).toBeDefined()
        
        if (expectedCoverId) {
          const coverId = result!.info.coverUrl!.match(/(\d+_[^.]+)/)?.[1]
          const subjectId = coverId?.split('_')[0]
          const expectedSubjectId = expectedCoverId.split('_')[0]
          
          expect(subjectId).toBe(expectedSubjectId)
        }
        
        if (expectedKeywords) {
          // 检查匹配结果是否包含预期关键词
          const matchedTitle = result!.info.title || ''
          const hasKeyword = expectedKeywords.some(kw => 
            matchedTitle.toLowerCase().includes(kw.toLowerCase())
          )
          expect(hasKeyword).toBe(true)
        }
        
        // 分数检查
        expect(result!.score).toBeGreaterThanOrEqual(30)
      },
      30000
    )
  })
})

// 导出测试用例供其他测试使用
export { WRONG_MATCH_CASES, VARIANT_CASES, COMPLEX_TITLE_CASES }
