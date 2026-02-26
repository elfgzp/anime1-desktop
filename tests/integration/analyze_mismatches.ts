/**
 * 分析数据库中已存储的封面与新搜索结果是否一致
 */

import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'
import * as sqlite3 from 'sqlite3'
import { open } from 'sqlite'

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
}

interface CoverCache {
  anime_id: string
  title: string
  cover_url: string
  cover_data: string
}

async function analyzeMismatches(limit = 20) {
  const dbPath = process.env.HOME + '/Library/Application Support/anime1-desktop-electron/anime1.db'
  
  const db = await open({
    filename: dbPath,
    driver: sqlite3.Database
  })
  
  // 获取所有有封面的记录
  const caches = await db.all<CoverCache[]>(`
    SELECT anime_id, title, cover_url, cover_data 
    FROM cover_cache 
    WHERE cover_url IS NOT NULL AND cover_url != ''
    LIMIT ?
  `, limit)
  
  await db.close()
  
  console.log(colors.blue(`分析了 ${caches.length} 条数据库记录`))
  console.log()
  
  let matchCount = 0
  let mismatchCount = 0
  
  const crawler = new BangumiCrawler()
  
  try {
    for (const cache of caches) {
      const coverData = JSON.parse(cache.cover_data)
      const storedTitle = coverData.title
      const storedCoverUrl = cache.cover_url
      
      // 重新搜索
      const result = await crawler.findBestMatch(cache.title, coverData.year)
      
      if (!result?.info?.coverUrl) {
        console.log(colors.red(`❌ [${cache.anime_id}] ${cache.title}`))
        console.log(`   存储的封面: ${storedCoverUrl?.substring(0, 60)}...`)
        console.log(`   新搜索: 未找到结果`)
        mismatchCount++
        continue
      }
      
      const newCoverUrl = result.info.coverUrl
      const newTitle = result.info.title
      
      // 提取封面ID进行比较
      const storedId = storedCoverUrl?.match(/(\d+_[^.]+)/)?.[1]
      const newId = newCoverUrl.match(/(\d+_[^.]+)/)?.[1]
      
      const isMatch = storedId && newId && storedId === newId
      
      if (isMatch) {
        console.log(colors.green(`✓ [${cache.anime_id}] ${cache.title}`))
        matchCount++
      } else {
        console.log(colors.red(`❌ [${cache.anime_id}] ${cache.title}`))
        console.log(`   存储的: ${storedTitle} -> ${storedCoverUrl?.substring(0, 50)}...`)
        console.log(`   新搜索: ${newTitle} -> ${newCoverUrl.substring(0, 50)}...`)
        console.log(`   分数: ${result.score}`)
        mismatchCount++
      }
      
      // 延迟避免请求过快
      await new Promise(r => setTimeout(r, 300))
    }
  } finally {
    crawler.close()
  }
  
  console.log()
  console.log(colors.blue('=============================================='))
  console.log(colors.green(`匹配: ${matchCount}`))
  console.log(colors.red(`不匹配: ${mismatchCount}`))
  console.log(colors.blue('=============================================='))
}

const limit = parseInt(process.argv[2]) || 20
analyzeMismatches(limit).catch(console.error)
