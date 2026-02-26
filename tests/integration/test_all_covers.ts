/**
 * 测试数据库中所有封面与新搜索结果的匹配情况
 */

import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
}

interface CoverData {
  id: string
  title: string
  stored_cover_id: string
  stored_title: string
  year: string
  cover_url: string
}

interface TestResult {
  id: string
  title: string
  storedCoverId: string
  storedTitle: string
  newCoverId?: string
  newTitle?: string
  score: number
  match: boolean
  error?: string
}

async function testAllCovers() {
  // 读取数据
  const dataPath = path.join(__dirname, '../../test-data/cover_cache.json')
  const caches: CoverData[] = JSON.parse(fs.readFileSync(dataPath, 'utf-8'))
  
  console.log(colors.blue(`==================================================`))
  console.log(colors.blue(`  数据库封面全面测试`))
  console.log(colors.blue(`  总计: ${caches.length} 条记录`))
  console.log(colors.blue(`==================================================`))
  console.log()
  
  const results: TestResult[] = []
  let matchCount = 0
  let mismatchCount = 0
  let notFoundCount = 0
  let errorCount = 0
  
  const crawler = new BangumiCrawler()
  
  // 测试限制（可以设置为 smaller 值来测试部分数据）
  const testLimit = process.env.TEST_LIMIT ? parseInt(process.env.TEST_LIMIT) : caches.length
  const testData = caches.slice(0, testLimit)
  
  try {
    for (let i = 0; i < testData.length; i++) {
      const cache = testData[i]
      
      if (i % 10 === 0) {
        process.stdout.write(`\r[${i + 1}/${testData.length}] 测试中... `)
      }
      
      try {
        const result = await crawler.findBestMatch(cache.title, cache.year)
        
        if (!result?.info?.coverUrl) {
          notFoundCount++
          results.push({
            id: cache.id,
            title: cache.title,
            storedCoverId: cache.stored_cover_id,
            storedTitle: cache.stored_title,
            score: 0,
            match: false,
            error: '未找到'
          })
          continue
        }
        
        const newCoverUrl = result.info.coverUrl
        const newCoverId = newCoverUrl.match(/(\d+_[^.]+)/)?.[1] || ''
        const newTitle = result.info.title
        const isMatch = cache.stored_cover_id === newCoverId
        
        if (isMatch) {
          matchCount++
        } else {
          mismatchCount++
        }
        
        results.push({
          id: cache.id,
          title: cache.title,
          storedCoverId: cache.stored_cover_id,
          storedTitle: cache.stored_title,
          newCoverId,
          newTitle,
          score: result.score,
          match: isMatch
        })
        
        // 延迟避免请求过快
        await new Promise(r => setTimeout(r, 150))
        
      } catch (error: any) {
        errorCount++
        results.push({
          id: cache.id,
          title: cache.title,
          storedCoverId: cache.stored_cover_id,
          storedTitle: cache.stored_title,
          score: 0,
          match: false,
          error: error.message
        })
      }
    }
  } finally {
    crawler.close()
  }
  
  console.log('\r' + ' '.repeat(50) + '\r')
  
  // 输出统计
  console.log(colors.blue(`==================================================`))
  console.log(colors.blue(`  统计结果`))
  console.log(colors.blue(`==================================================`))
  console.log(`总测试数: ${testData.length}`)
  console.log(colors.green(`✓ 匹配: ${matchCount} (${(matchCount/testData.length*100).toFixed(1)}%)`))
  console.log(colors.red(`❌ 不匹配: ${mismatchCount} (${(mismatchCount/testData.length*100).toFixed(1)}%)`))
  console.log(colors.yellow(`⚠ 未找到: ${notFoundCount} (${(notFoundCount/testData.length*100).toFixed(1)}%)`))
  console.log(colors.gray(`  错误: ${errorCount}`))
  console.log(colors.blue(`==================================================`))
  
  // 保存详细结果到文件
  const outputDir = path.join(__dirname, '../../test-results')
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true })
  }
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const outputFile = path.join(outputDir, `cover-test-${timestamp}.json`)
  
  fs.writeFileSync(outputFile, JSON.stringify({
    summary: {
      total: testData.length,
      match: matchCount,
      mismatch: mismatchCount,
      notFound: notFoundCount,
      error: errorCount
    },
    results: results
  }, null, 2))
  
  console.log(`\n详细结果已保存到: ${outputFile}`)
  
  // 输出不匹配的详情（前30个）
  const mismatches = results.filter(r => !r.match && !r.error)
  if (mismatches.length > 0) {
    console.log(colors.red(`\n不匹配详情（前30个）:`))
    console.log(colors.red(`==================================================`))
    for (const m of mismatches.slice(0, 30)) {
      console.log(`[${m.id}] ${m.title}`)
      console.log(`  存储: ${m.storedTitle} (${m.storedCoverId})`)
      console.log(`  新搜: ${m.newTitle} (${m.newCoverId}) score=${m.score}`)
    }
    if (mismatches.length > 30) {
      console.log(colors.gray(`  ... 还有 ${mismatches.length - 30} 个不匹配`))
    }
  }
  
  // 输出未找到的详情
  const notFounds = results.filter(r => r.error === '未找到')
  if (notFounds.length > 0) {
    console.log(colors.yellow(`\n未找到详情（前15个）:`))
    console.log(colors.yellow(`==================================================`))
    for (const n of notFounds.slice(0, 15)) {
      console.log(`[${n.id}] ${n.title}`)
    }
    if (notFounds.length > 15) {
      console.log(colors.gray(`  ... 还有 ${notFounds.length - 15} 个未找到`))
    }
  }
  
  return results
}

// 运行测试
testAllCovers().catch(console.error)
