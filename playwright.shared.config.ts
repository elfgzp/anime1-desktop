/**
 * Playwright E2E 测试配置 - 共享实例模式
 */
import { defineConfig } from '@playwright/test'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/shared-*.spec.ts',  // 只运行共享实例测试
  fullyParallel: false,  // 禁用并行
  workers: 1,  // 单 worker
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,  // CI 环境下重试一次
  reporter: [
    ['html', { outputFolder: 'e2e-report' }],
    ['list']
  ],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  globalSetup: resolve(__dirname, './e2e/global-setup.ts'),
  globalTeardown: resolve(__dirname, './e2e/global-teardown.ts'),
})
