/**
 * Playwright E2E 测试配置
 * 
 * 用于直接测试 Electron 应用
 */
import { defineConfig, devices } from '@playwright/test'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false, // Electron 测试通常需要串行执行
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Electron 应用通常只能有一个实例
  reporter: [
    ['html', { outputFolder: 'e2e-report' }],
    ['list']
  ],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'electron',
      use: {
        // Electron 特定的配置在 fixture 中处理
      },
    },
  ],
  // 全局超时设置
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
})
