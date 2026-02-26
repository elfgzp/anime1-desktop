/**
 * Playwright 全局 teardown
 * 
 * 在所有测试结束后执行一次
 */
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { rm } from 'fs/promises'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const TEST_DATA_DIR = resolve(__dirname, '../test-data/e2e')

async function globalTeardown() {
  console.log('[E2E] Global teardown started...')
  
  // 清理测试数据
  try {
    await rm(TEST_DATA_DIR, { recursive: true, force: true })
    console.log('[E2E] Cleaned test data directory')
  } catch (error) {
    console.warn('[E2E] Failed to clean test data:', error)
  }
  
  console.log('[E2E] Global teardown completed')
}

export default globalTeardown
