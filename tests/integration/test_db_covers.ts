/**
 * 测试数据库中存储的封面与新搜索结果是否匹配
 */

import { BangumiCrawler } from '../../src/main/services/crawler/bangumi'

const colors = {
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  blue: (text: string) => `\x1b[34m${text}\x1b[0m`,
  gray: (text: string) => `\x1b[90m${text}\x1b[0m`,
}

// 从数据库查询的数据
const TEST_CASES = [
  { id: '1646', title: '秘密的偶像公主 第二季', storedCoverId: '468758_A1XtM', storedTitle: '秘密的偶像公主 第二季', year: '2025' },
  { id: '1793', title: '午夜的傾心旋律', storedCoverId: '544109_U7B7C', storedTitle: '午夜的傾心旋律', year: '2026' },
  { id: '1827', title: '為了疼愛最推的義兄，我要長久活下去！', storedCoverId: '567362_Fc0ZT', storedTitle: '為了疼愛最推的義兄，我要長久活下去！', year: '2026' },
  { id: '1795', title: '身為魔族的我 想向勇者小隊的可愛女孩告白', storedCoverId: '525816_xDas0', storedTitle: '身為魔族的我 想向勇者小隊的可愛女孩告白', year: '2026' },
  { id: '1794', title: '異世界的處置依社畜而定', storedCoverId: '522370_FFyEr', storedTitle: '異世界的處置依社畜而定', year: '2026' },
  { id: '1819', title: '公主殿下，「拷問」的時間到了 第二季', storedCoverId: '547964_LLWNK', storedTitle: '公主殿下，「拷問」的時間到了 第二季', year: '2026' },
  { id: '1812', title: '勇者之渣', storedCoverId: '529356_3h6s5', storedTitle: '勇者之渣', year: '2026' },
  { id: '1757', title: '藍色管弦樂 第二季', storedCoverId: '483357_RlBS3', storedTitle: '藍色管弦樂 第二季', year: '2025' },
  { id: '1572', title: 'Fate/strange Fake', storedCoverId: '449507_c8ZSp', storedTitle: 'Fate/strange Fake', year: '2024' },
  { id: '1815', title: '死亡帳號', storedCoverId: '540122_E8V3E', storedTitle: '死亡帳號', year: '2026' },
  { id: '1574', title: '魔王 2099', storedCoverId: '479900_42g22', storedTitle: '魔王 2099', year: '2024' },
  { id: '1580', title: 'BLUE LOCK 藍色監獄 VS. U-20 日本代表隊', storedCoverId: '473724_CqntD', storedTitle: 'BLUE LOCK 藍色監獄 VS. U-20 日本代表隊', year: '2024' },
  { id: '1565', title: 'Re:從零開始的異世界生活 第三季', storedCoverId: '424364_H3p0J', storedTitle: 'Re:從零開始的異世界生活 第三季', year: '2024' },
  { id: '1540', title: '刀劍神域外傳 Gun Gale Online 第二季', storedCoverId: '448233_X8O60', storedTitle: '刀劍神域外傳 Gun Gale Online 第二季', year: '2024' },
  { id: '1524', title: '神之塔 第二季', storedCoverId: '485111_66N66', storedTitle: '神之塔 第二季', year: '2024' },
  { id: '1507', title: '2.5次元的誘惑', storedCoverId: '426443_7N8P9', storedTitle: '2.5次元的誘惑', year: '2024' },
  { id: '1508', title: '來自貓的遺書', storedCoverId: '488244_UppS7', storedTitle: '來自貓的遺書', year: '2024' },
  { id: '1510', title: '這個世界漏洞百出', storedCoverId: '464376_7vjFi', storedTitle: '這個世界漏洞百出', year: '2024' },
  { id: '1511', title: '【我推的孩子】第二季', storedCoverId: '443399_8ZY2K', storedTitle: '【我推的孩子】第二季', year: '2024' },
  { id: '1514', title: '鹿乃子乃子乃子虎視眈眈', storedCoverId: '507450_6Mm40', storedTitle: '鹿乃子乃子乃子虎視眈眈', year: '2024' },
]

async function runTests() {
  console.log(colors.blue('=================================================='))
  console.log(colors.blue('  数据库封面与新搜索结果对比测试'))
  console.log(colors.blue('=================================================='))
  console.log()
  
  let matchCount = 0
  let mismatchCount = 0
  let notFoundCount = 0
  
  const crawler = new BangumiCrawler()
  
  try {
    for (const test of TEST_CASES) {
      const result = await crawler.findBestMatch(test.title, test.year)
      
      if (!result?.info?.coverUrl) {
        console.log(colors.yellow(`⚠ [${test.id}] ${test.title}`))
        console.log(`   存储: ${test.storedTitle} (${test.storedCoverId})`)
        console.log(`   新搜: 未找到`)
        notFoundCount++
        continue
      }
      
      // 提取新封面的ID
      const newCoverId = result.info.coverUrl.match(/(\d+_[^.]+)/)?.[1]
      const isMatch = newCoverId === test.storedCoverId
      
      if (isMatch) {
        console.log(colors.green(`✓ [${test.id}] ${test.title}`))
        matchCount++
      } else {
        console.log(colors.red(`❌ [${test.id}] ${test.title}`))
        console.log(`   存储: ${test.storedTitle} (${test.storedCoverId})`)
        console.log(`   新搜: ${result.info.title} (${newCoverId}) score=${result.score}`)
        mismatchCount++
      }
      
      // 延迟避免请求过快
      await new Promise(r => setTimeout(r, 300))
    }
  } finally {
    crawler.close()
  }
  
  console.log()
  console.log(colors.blue('=================================================='))
  console.log(colors.blue('  统计结果'))
  console.log(colors.blue('=================================================='))
  console.log(`总测试数: ${TEST_CASES.length}`)
  console.log(colors.green(`✓ 匹配: ${matchCount}`))
  console.log(colors.red(`❌ 不匹配: ${mismatchCount}`))
  console.log(colors.yellow(`⚠ 未找到: ${notFoundCount}`))
  console.log(colors.blue('=================================================='))
}

runTests().catch(console.error)
