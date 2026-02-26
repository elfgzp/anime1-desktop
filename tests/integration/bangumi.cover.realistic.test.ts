/**
 * @integration
 * Bangumi 封面匹配现实测试
 * 
 * 测试真实数据库中的案例，包括已知的问题案例。
 * 这些测试验证当前实现的最佳表现，而非期望完美匹配。
 * 
 * 运行: npx vitest run tests/integration/bangumi.cover.realistic.test.ts
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'

// ===== 应该正确匹配的案例（正面测试）=====
const SHOULD_MATCH_CASES = [
  {
    id: '1646',
    title: '秘密的偶像公主 第二季',
    expectedCoverId: '468758',
    minScore: 30,
    description: '繁体标题应匹配简体结果'
  },
  {
    id: '1793',
    title: '午夜的傾心旋律',
    expectedCoverId: '544109',
    minScore: 30,
    description: '繁体标题应匹配简体结果'
  },
  {
    id: '1813',
    title: '轉生之後的我變成了龍蛋～目標是世界最強～',
    expectedCoverId: '544106',
    minScore: 30,
    description: '长标题应正确提取核心词匹配'
  },
  {
    id: '1572',
    title: 'Fate/strange Fake',
    expectedCoverId: '443831',
    minScore: 50,
    description: '英文标题应精确匹配'
  },
  {
    id: '1757',
    title: '藍色管弦樂 第二季',
    expectedCoverId: '458673',
    minScore: 30,
    description: '繁体季度应匹配简体季度'
  }
]

// ===== 已知问题案例（数据源差异）=====
const KNOWN_ISSUE_CASES = [
  {
    id: '1742',
    title: '娑婆氣',
    expectedCoverId: '340164',  // Bangumi 简体"娑婆气"
    issue: '繁简差异',
    description: 'Anime1使用"娑婆氣"，Bangumi使用"娑婆气"'
  },
  {
    id: '1811',
    title: '和機器人啪啪啪能算在經驗人數裡嗎？？',
    expectedCoverId: '173020',  // "园园和机器人"
    issue: '标题完全不同',
    description: 'Anime1使用长标题，Bangumi使用简短别名'
  },
  {
    id: '206081',
    title: '罪惡之淵',
    expectedCoverId: '54705',  // "断裁分离的罪恶之剪"
    issue: '标题完全不同',
    description: 'Anime1使用日文直译，Bangumi使用中文译名'
  }
]

// ===== 不应匹配到明显错误结果的案例 =====
const SHOULD_NOT_MATCH_WRONG_CASES = [
  {
    id: 'test_not_dramatic_murder',
    title: '娑婆氣',
    wrongIds: ['100557'],  // 戏剧性谋杀
    description: '不应该匹配到"戏剧性谋杀"'
  },
  {
    id: 'test_not_guilty_crown',
    title: '罪惡之淵',
    wrongIds: ['18635'],  // 罪恶王冠
    description: '不应该匹配到"罪恶王冠"'
  },
  {
    id: 'test_not_love_death_robots',
    title: '和機器人啪啪啪能算在經驗人數裡嗎？？',
    wrongIds: ['274613'],  // 爱、死亡 & 机器人
    description: '不应该匹配到"爱、死亡 & 机器人"'
  }
]

describe('Bangumi 封面匹配 - 正面测试', () => {
  let crawler: BangumiCrawler

  beforeAll(() => {
    crawler = new BangumiCrawler()
  })

  afterAll(() => {
    crawler.close()
  })

  it.each(SHOULD_MATCH_CASES)(
    '[$id] $title - $description',
    async ({ title, expectedCoverId, minScore }) => {
      const result = await crawler.findBestMatch(title)
      
      expect(result).not.toBeNull()
      expect(result!.info.coverUrl).toBeDefined()
      
      const coverId = result!.info.coverUrl!.match(/(\d+_[^.]+)/)?.[1]
      const subjectId = coverId?.split('_')[0]
      
      expect(subjectId).toBe(expectedCoverId)
      expect(result!.score).toBeGreaterThanOrEqual(minScore)
    },
    30000
  )
})

describe('Bangumi 封面匹配 - 已知问题', () => {
  let crawler: BangumiCrawler

  beforeAll(() => {
    crawler = new BangumiCrawler()
  })

  afterAll(() => {
    crawler.close()
  })

  it.each(KNOWN_ISSUE_CASES)(
    '[$id] $title - Issue: $issue',
    async ({ title, expectedCoverId, issue }) => {
      const result = await crawler.findBestMatch(title)
      
      // 对于这些已知问题，我们只验证：
      // 1. 代码不崩溃
      // 2. 返回了结果
      expect(result).not.toBeNull()
      
      if (result?.info.coverUrl) {
        const coverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        // 如果是繁简差异，可能匹配到正确结果
        // 如果是标题完全不同，则不强求匹配
        if (issue === '繁简差异') {
          expect(subjectId).toBe(expectedCoverId)
        } else {
          // 对于标题完全不同的情况，记录但不失败
          console.log(`  匹配结果: ${result.info.title} (${subjectId})`)
          console.log(`  期望值: ${expectedCoverId}`)
        }
      }
    },
    30000
  )
})

describe('Bangumi 封面匹配 - 不应匹配错误', () => {
  let crawler: BangumiCrawler

  beforeAll(() => {
    crawler = new BangumiCrawler()
  })

  afterAll(() => {
    crawler.close()
  })

  it.each(SHOULD_NOT_MATCH_WRONG_CASES)(
    '[$id] $title - $description',
    async ({ title, wrongIds }) => {
      const result = await crawler.findBestMatch(title)
      
      expect(result).not.toBeNull()
      
      if (result?.info.coverUrl) {
        const coverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        // 确保没有匹配到已知的错误结果
        expect(wrongIds).not.toContain(subjectId)
      }
    },
    30000
  )
})

describe('Bangumi 封面匹配 - 分数验证', () => {
  let crawler: BangumiCrawler

  beforeAll(() => {
    crawler = new BangumiCrawler()
  })

  afterAll(() => {
    crawler.close()
  })

  it('相似度分数应在合理范围内', async () => {
    const testCases = [
      { title: '鬼灭之刃', expectedMinScore: 80 },
      { title: '间谍过家家', expectedMinScore: 80 },
      { title: '进击的巨人', expectedMinScore: 80 }
    ]

    for (const { title, expectedMinScore } of testCases) {
      const result = await crawler.findBestMatch(title)
      expect(result).not.toBeNull()
      expect(result!.score).toBeGreaterThanOrEqual(expectedMinScore)
    }
  }, 60000)
})

// 导出测试用例供其他测试使用
export { SHOULD_MATCH_CASES, KNOWN_ISSUE_CASES, SHOULD_NOT_MATCH_WRONG_CASES }
