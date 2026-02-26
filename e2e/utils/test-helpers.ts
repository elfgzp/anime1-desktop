/**
 * 测试辅助函数
 */
import type { Page } from '@playwright/test'

/**
 * 等待元素包含特定文本
 */
export async function waitForText(
  page: Page,
  selector: string,
  text: string,
  timeout = 10000
): Promise<void> {
  await page.waitForFunction(
    ({ sel, txt }) => {
      const element = document.querySelector(sel)
      return element && element.textContent?.includes(txt)
    },
    { sel: selector, txt: text },
    { timeout }
  )
}

/**
 * 等待元素可见并点击
 */
export async function clickWhenVisible(
  page: Page,
  selector: string,
  timeout = 10000
): Promise<void> {
  await page.locator(selector).waitFor({ state: 'visible', timeout })
  await page.locator(selector).click()
}

/**
 * 安全地填写表单字段
 */
export async function fillField(
  page: Page,
  selector: string,
  value: string,
  timeout = 10000
): Promise<void> {
  const locator = page.locator(selector)
  await locator.waitFor({ state: 'visible', timeout })
  await locator.fill(value)
}

/**
 * 获取元素属性
 */
export async function getElementAttribute(
  page: Page,
  selector: string,
  attribute: string
): Promise<string | null> {
  return await page.locator(selector).getAttribute(attribute)
}

/**
 * 检查元素是否存在且可见
 */
export async function isElementVisible(
  page: Page,
  selector: string
): Promise<boolean> {
  const locator = page.locator(selector)
  const count = await locator.count()
  if (count === 0) return false
  return await locator.isVisible()
}

/**
 * 等待加载完成（loading 元素消失）
 */
export async function waitForLoadingComplete(
  page: Page,
  loadingSelector = '.loading, .el-loading-mask, [class*="loading"]',
  timeout = 30000
): Promise<void> {
  try {
    await page.waitForSelector(loadingSelector, { 
      state: 'detached', 
      timeout 
    })
  } catch {
    // 加载元素可能不存在，忽略错误
  }
}

/**
 * 截取元素截图
 */
export async function screenshotElement(
  page: Page,
  selector: string,
  path: string
): Promise<void> {
  const element = page.locator(selector)
  await element.waitFor({ state: 'visible' })
  await element.screenshot({ path })
}

/**
 * 模拟网络延迟
 */
export async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 重试函数直到成功或超时
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; delay?: number } = {}
): Promise<T> {
  const { maxAttempts = 3, delay: delayMs = 1000 } = options
  
  let lastError: Error | undefined
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      if (i < maxAttempts - 1) {
        await delay(delayMs)
      }
    }
  }
  
  throw lastError
}

/**
 * 生成随机测试数据
 */
export function generateTestData() {
  const timestamp = Date.now()
  return {
    id: `test_${timestamp}`,
    title: `Test Title ${timestamp}`,
    description: `Test Description ${timestamp}`,
    email: `test_${timestamp}@example.com`,
    username: `user_${timestamp}`,
  }
}

/**
 * 清理测试数据（用于测试后清理）
 */
export async function cleanupTestData(
  page: Page,
  testIds: string[]
): Promise<void> {
  for (const id of testIds) {
    try {
      // 通过 IPC 清理测试数据
      await page.evaluate(async (testId) => {
        // 尝试删除相关的测试收藏
        try {
          await window.api.favorite.remove({ animeId: testId })
        } catch {
          // 忽略错误
        }
      }, id)
    } catch {
      // 忽略清理错误
    }
  }
}
