/**
 * 运行 Bangumi 封面匹配测试
 * 
 * 使用: npx tsx tests/integration/run-cover-tests.ts
 */

import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
}

// 应该正确匹配的案例
const SHOULD_MATCH_CASES = [
  { id: '1646', title: '秘密的偶像公主 第二季', expectedCoverId: '468758', minScore: 30 },
  { id: '1793', title: '午夜的傾心旋律', expectedCoverId: '544109', minScore: 30 },
  { id: '1813', title: '轉生之後的我變成了龍蛋～目標是世界最強～', expectedCoverId: '544106', minScore: 30 },
  { id: '1572', title: 'Fate/strange Fake', expectedCoverId: '443831', minScore: 50 },
  { id: '1757', title: '藍色管弦樂 第二季', expectedCoverId: '458673', minScore: 30 },
]

// 已知问题案例
const KNOWN_ISSUE_CASES = [
  { id: '1742', title: '娑婆氣', expectedCoverId: '340164', issue: '繁简差异' },
  { id: '1811', title: '和機器人啪啪啪能算在經驗人數裡嗎？？', expectedCoverId: '173020', issue: '标题完全不同' },
  { id: '206081', title: '罪惡之淵', expectedCoverId: '54705', issue: '标题完全不同' },
]

// 不应匹配到错误结果
const SHOULD_NOT_MATCH_WRONG_CASES = [
  { id: '1742', title: '娑婆氣', wrongIds: ['100557'], wrongTitle: '戏剧性谋杀' },
  { id: '206081', title: '罪惡之淵', wrongIds: ['18635'], wrongTitle: '罪恶王冠' },
  { id: '1811', title: '和機器人啪啪啪能算在經驗人數裡嗎？？', wrongIds: ['274613'], wrongTitle: '爱、死亡 & 机器人' },
]

async function runTests() {
  console.log(colors.blue('=================================================='))
  console.log(colors.blue('  Bangumi 封面匹配测试'))
  console.log(colors.blue('=================================================='))
  console.log()

  const crawler = new BangumiCrawler()
  let passed = 0
  let failed = 0
  let warnings = 0

  try {
    // 测试 1: 应该正确匹配的案例
    console.log(colors.blue('【测试组 1】应该正确匹配的案例'))
    console.log(colors.blue('--------------------------------------------------'))

    for (const testCase of SHOULD_MATCH_CASES) {
      process.stdout.write(`  [${testCase.id}] ${testCase.title}... `)
      
      try {
        const result = await crawler.findBestMatch(testCase.title)
        
        if (!result?.info?.coverUrl) {
          console.log(colors.red('✗ 未找到结果'))
          failed++
          continue
        }
        
        const coverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        if (subjectId === testCase.expectedCoverId && result.score >= testCase.minScore) {
          console.log(colors.green(`✓ (score: ${result.score})`))
          passed++
        } else {
          console.log(colors.red(`✗ 期望 ${testCase.expectedCoverId}, 得到 ${subjectId} (score: ${result.score})`))
          failed++
        }
      } catch (error: any) {
        console.log(colors.red(`✗ 错误: ${error.message}`))
        failed++
      }
      
      await new Promise(r => setTimeout(r, 200))
    }
    console.log()

    // 测试 2: 已知问题案例
    console.log(colors.blue('【测试组 2】已知问题案例'))
    console.log(colors.blue('--------------------------------------------------'))

    for (const testCase of KNOWN_ISSUE_CASES) {
      process.stdout.write(`  [${testCase.id}] ${testCase.title}... `)
      
      try {
        const result = await crawler.findBestMatch(testCase.title)
        
        if (!result?.info?.coverUrl) {
          console.log(colors.yellow(`⚠ 未找到结果 (${testCase.issue})`))
          warnings++
          continue
        }
        
        const coverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        if (subjectId === testCase.expectedCoverId) {
          console.log(colors.green(`✓ 已修复! (score: ${result.score})`))
          passed++
        } else {
          console.log(colors.yellow(`⚠ ${testCase.issue}: 得到 ${result.info.title} (${subjectId})`))
          warnings++
        }
      } catch (error: any) {
        console.log(colors.red(`✗ 错误: ${error.message}`))
        failed++
      }
      
      await new Promise(r => setTimeout(r, 200))
    }
    console.log()

    // 测试 3: 不应匹配到错误结果
    console.log(colors.blue('【测试组 3】不应匹配到错误结果'))
    console.log(colors.blue('--------------------------------------------------'))

    for (const testCase of SHOULD_NOT_MATCH_WRONG_CASES) {
      process.stdout.write(`  [${testCase.id}] 不应匹配到"${testCase.wrongTitle}"... `)
      
      try {
        const result = await crawler.findBestMatch(testCase.title)
        
        if (!result?.info?.coverUrl) {
          console.log(colors.green('✓ 未返回结果（安全）'))
          passed++
          continue
        }
        
        const coverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
        const subjectId = coverId?.split('_')[0]
        
        if (testCase.wrongIds.includes(subjectId || '')) {
          console.log(colors.red(`✗ 错误匹配到 ${testCase.wrongTitle} (${subjectId})`))
          failed++
        } else {
          console.log(colors.green(`✓ 匹配到 ${result.info.title} (${subjectId})`))
          passed++
        }
      } catch (error: any) {
        console.log(colors.red(`✗ 错误: ${error.message}`))
        failed++
      }
      
      await new Promise(r => setTimeout(r, 200))
    }
    console.log()

  } finally {
    crawler.close()
  }

  // 统计
  console.log(colors.blue('=================================================='))
  console.log(colors.blue('  测试结果'))
  console.log(colors.blue('=================================================='))
  console.log(`${colors.green(`✓ 通过: ${passed}`)}`)
  console.log(`${colors.red(`✗ 失败: ${failed}`)}`)
  console.log(`${colors.yellow(`⚠ 警告: ${warnings}`)}`)
  console.log(colors.blue('=================================================='))

  process.exit(failed > 0 ? 1 : 0)
}

runTests().catch(console.error)
