/**
 * @integration
 * Bangumi 集成测试
 * 
 * 测试 BangumiCrawler 是否能正确搜索到封面和详情
 * 对应 Python 版本: cover_finder.py 的测试用例
 * 
 * 运行: npx ts-node tests/integration/bangumi.integration.test.ts
 */

import { BangumiCrawler, findBangumiCover } from '../../src/main/services/crawler/bangumi'

// 测试数据 - 与 Python 版本保持一致
const TEST_CASES = [
  { title: '鬼灭之刃', year: '2019', expectedCover: true },
  { title: '进击的巨人', year: '2013', expectedCover: true },
  { title: '间谍过家家', year: '2022', expectedCover: true },
  { title: 'Chainsaw Man', year: '2022', expectedCover: true },
  { title: '咒术回战', year: '2020', expectedCover: true },
  // 带季数的测试 - 验证核心关键词提取
  { title: '鬼灭之刃 第二季', year: '2021', expectedCover: true },
  { title: '进击的巨人 最终季', year: '2020', expectedCover: true },
  // 繁体中文测试
  { title: '鬼滅之刃', year: '2019', expectedCover: true },
  // 边缘情况
  { title: '不存在的动画 XYZ123', year: '2024', expectedCover: false },
]

// 颜色输出
const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
}

async function runTests() {
  console.log(colors.blue('=============================================='))
  console.log(colors.blue('  Bangumi 集成测试'))
  console.log(colors.blue('=============================================='))
  console.log()

  const crawler = new BangumiCrawler()
  let passed = 0
  let failed = 0

  for (const testCase of TEST_CASES) {
    const { title, year, expectedCover } = testCase
    
    try {
      console.log(`测试: "${title}" (year=${year})`)
      
      const result = await crawler.findBestMatch(title, year)
      
      const foundCover = result?.info?.coverUrl ? true : false
      const score = result?.score ?? 0
      const matchedTitle = result?.info?.title ?? 'N/A'
      
      // 验证结果
      const success = foundCover === expectedCover
      
      if (success) {
        console.log(colors.green(`  ✓ PASS`))
        passed++
      } else {
        console.log(colors.red(`  ✗ FAIL`))
        failed++
      }
      
      console.log(`    匹配标题: ${matchedTitle}`)
      console.log(`    匹配分数: ${score.toFixed(1)}`)
      console.log(`    找到封面: ${foundCover}`)
      
      if (result?.info?.coverUrl) {
        console.log(`    封面URL: ${result.info.coverUrl.substring(0, 60)}...`)
      }
      
      if (result?.info?.rank) {
        console.log(`    Bangumi排名: #${result.info.rank}`)
      }
      
      if (result?.info?.rating) {
        console.log(`    评分: ${result.info.rating}`)
      }
      
      // 延迟避免请求过快
      await new Promise(r => setTimeout(r, 500))
      
    } catch (error) {
      console.log(colors.red(`  ✗ ERROR: ${error}`))
      failed++
    }
    
    console.log()
  }

  crawler.close()

  // 测试便捷函数
  console.log(colors.blue('----------------------------------------------'))
  console.log('测试便捷函数 findBangumiCover():')
  try {
    const { coverUrl, info } = await findBangumiCover('间谍过家家', '2022')
    if (coverUrl && info) {
      console.log(colors.green('  ✓ PASS'))
      console.log(`    标题: ${info.title}`)
      console.log(`    封面: ${coverUrl.substring(0, 60)}...`)
      passed++
    } else {
      console.log(colors.red('  ✗ FAIL: 未找到封面或详情'))
      failed++
    }
  } catch (error) {
    console.log(colors.red(`  ✗ ERROR: ${error}`))
    failed++
  }

  console.log()
  console.log(colors.blue('=============================================='))
  console.log(colors.green(`  通过: ${passed}`))
  console.log(colors.red(`  失败: ${failed}`))
  console.log(colors.blue('=============================================='))

  process.exit(failed > 0 ? 1 : 0)
}

runTests()
