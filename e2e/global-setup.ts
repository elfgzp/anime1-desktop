/**
 * Playwright 全局 setup
 * 
 * 在所有测试开始前执行一次
 */
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { mkdir, rm } from 'fs/promises'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const TEST_DATA_DIR = resolve(__dirname, '../test-data/e2e')

async function globalSetup() {
  console.log('[E2E] Global setup started...')
  
  // 清理旧的测试数据
  try {
    await rm(TEST_DATA_DIR, { recursive: true, force: true })
    console.log('[E2E] Cleaned old test data')
  } catch {
    // 目录可能不存在，忽略错误
  }
  
  // 创建新的测试数据目录
  await mkdir(TEST_DATA_DIR, { recursive: true })
  console.log('[E2E] Created test data directory:', TEST_DATA_DIR)
  
  // 检查 Electron 是否已构建
  const { stat } = await import('fs/promises')
  const mainPath = resolve(__dirname, '../dist-electron/main/index.js')
  
  try {
    await stat(mainPath)
    console.log('[E2E] Electron build found at:', mainPath)
  } catch {
    console.warn('[E2E] Warning: Electron build not found at:', mainPath)
    console.warn('[E2E] Tests will run in development mode (slower)')
  }
  
  console.log('[E2E] Global setup completed')
}

export default globalSetup
