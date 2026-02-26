/**
 * @integration
 * Python vs TypeScript 封面搜索结果对比测试
 * 
 * 运行: npx vite-node tests/integration/compare_with_python.test.ts
 */

import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'
import { execSync } from 'child_process'

// 测试数据（从数据库中选取的真实案例）
const TEST_CASES = [
  { id: '1646', title: '秘密的偶像公主 第二季', year: '2025', season: '春' },
  { id: '1793', title: '午夜的傾心旋律', year: '2026', season: '冬' },
  { id: '1827', title: '為了疼愛最推的義兄，我要長久活下去！', year: '2026', season: '冬' },
  { id: '1795', title: '身為魔族的我 想向勇者小隊的可愛女孩告白', year: '2026', season: '冬' },
  { id: '1794', title: '異世界的處置依社畜而定', year: '2026', season: '冬' },
  { id: '1819', title: '公主殿下，「拷問」的時間到了 第二季', year: '2026', season: '冬' },
  { id: '1812', title: '勇者之渣', year: '2026', season: '冬' },
  { id: '1757', title: '藍色管弦樂 第二季', year: '2025', season: '秋' },
  { id: '1572', title: 'Fate/strange Fake', year: '2024', season: '秋' },
  { id: '1815', title: '死亡帳號', year: '2026', season: '冬' },
  // 热门动漫
  { id: '1001', title: '鬼灭之刃', year: '2019' },
  { id: '1002', title: '进击的巨人', year: '2013' },
  { id: '1003', title: '间谍过家家', year: '2022' },
]

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
}

async function searchWithTS(title: string, year?: string): Promise<any> {
  const crawler = new BangumiCrawler()
  try {
    const result = await crawler.findBestMatch(title, year)
    return {
      title: result?.info?.title,
      coverUrl: result?.info?.coverUrl,
      score: result?.score,
      found: !!result?.info?.coverUrl
    }
  } finally {
    crawler.close()
  }
}

function searchWithPython(title: string, year?: string): any {
  try {
    const script = `
import sys
sys.path.insert(0, '/Users/gzp/Github/anime1-desktop/src')
from parser.cover_finder import cover_finder

result = cover_finder._search_bangumi("${title.replace(/"/g, '\\"')}")
if result:
    print(f"TITLE:{result.get('title', '')}")
    print(f"COVER:{result.get('cover_url', '')}")
    print(f"SCORE:{result.get('score', 0)}")
else:
    print("NOT_FOUND")
`
    const output = execSync(`cd /Users/gzp/Github/anime1-desktop && uv run python3 -c "${script}"`, {
      encoding: 'utf8',
      timeout: 30000
    })
    
    const lines = output.trim().split('\n')
    const result: any = { found: false }
    
    for (const line of lines) {
      if (line.startsWith('TITLE:')) {
        result.title = line.substring(6)
      } else if (line.startsWith('COVER:')) {
        result.coverUrl = line.substring(6)
        result.found = !!result.coverUrl
      } else if (line.startsWith('SCORE:')) {
        result.score = parseFloat(line.substring(6))
      }
    }
    
    return result
  } catch (e: any) {
    return { found: false, error: e.message }
  }
}

async function runComparison() {
  console.log(colors.blue('=============================================='))
  console.log(colors.blue('  Python vs TypeScript 封面搜索对比'))
  console.log(colors.blue('=============================================='))
  console.log()
  
  let tsFound = 0
  let pyFound = 0
  let bothMatch = 0
  let mismatch = 0
  
  for (const testCase of TEST_CASES) {
    const { id, title, year, season } = testCase
    
    console.log(`测试 #${id}: ${title}`)
    console.log(colors.gray(`  年份: ${year || 'N/A'}, 季节: ${season || 'N/A'}`))
    
    // TypeScript 搜索
    const tsResult = await searchWithTS(title, year)
    
    // Python 搜索
    const pyResult = searchWithPython(title, year)
    
    // 统计
    if (tsResult.found) tsFound++
    if (pyResult.found) pyFound++
    
    // 判断是否匹配
    const tsCoverId = tsResult.coverUrl?.match(/(\d+_[^.]+)/)?.[1] || ''
    const pyCoverId = pyResult.coverUrl?.match(/(\d+_[^.]+)/)?.[1] || ''
    const isMatch = tsCoverId && pyCoverId && tsCoverId === pyCoverId
    
    if (isMatch) {
      bothMatch++
      console.log(colors.green('  ✓ 匹配'))
    } else {
      mismatch++
      console.log(colors.red('  ✗ 不匹配'))
    }
    
    // 显示结果
    console.log(`  TypeScript: ${tsResult.found ? '找到' : '未找到'} ${tsResult.coverUrl ? '(' + tsResult.coverUrl.substring(0, 50) + '...)' : ''}`)
    console.log(`  Python:     ${pyResult.found ? '找到' : '未找到'} ${pyResult.coverUrl ? '(' + pyResult.coverUrl.substring(0, 50) + '...)' : ''}`)
    
    if (!isMatch && tsResult.found && pyResult.found) {
      console.log(colors.yellow(`  警告: 封面不匹配!`))
      console.log(`    TS: ${tsResult.title}`)
      console.log(`    PY: ${pyResult.title}`)
    }
    
    console.log()
    
    // 延迟避免请求过快
    await new Promise(r => setTimeout(r, 500))
  }
  
  console.log(colors.blue('=============================================='))
  console.log(colors.blue('  统计结果'))
  console.log(colors.blue('=============================================='))
  console.log(`总测试数: ${TEST_CASES.length}`)
  console.log(`TypeScript 找到: ${tsFound}`)
  console.log(`Python 找到: ${pyFound}`)
  console.log(colors.green(`匹配: ${bothMatch}`))
  console.log(colors.red(`不匹配: ${mismatch}`))
  console.log(colors.blue('=============================================='))
}

runComparison().catch(console.error)
