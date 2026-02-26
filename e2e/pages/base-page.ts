/**
 * 基础页面对象
 * 
 * 所有页面类的基类
 */
import type { Page, Locator } from '@playwright/test'
import { expect } from '../fixtures'

export class BasePage {
  constructor(protected page: Page) {}

  /**
   * 等待页面加载完成
   */
  async waitForLoaded(): Promise<void> {
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * 截图
   */
  async screenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `./e2e-report/screenshots/${name}.png`,
      fullPage: true 
    })
  }

  /**
   * 检查元素是否存在
   */
  async hasElement(selector: string): Promise<boolean> {
    return await this.page.locator(selector).count() > 0
  }

  /**
   * 安全地点击元素（等待元素可见后点击）
   */
  async safeClick(selector: string): Promise<void> {
    const locator = this.page.locator(selector)
    await locator.waitFor({ state: 'visible' })
    await locator.click()
  }

  /**
   * 安全地填写输入框
   */
  async safeFill(selector: string, text: string): Promise<void> {
    const locator = this.page.locator(selector)
    await locator.waitFor({ state: 'visible' })
    await locator.fill(text)
  }

  /**
   * 等待元素出现
   */
  async waitForElement(selector: string, timeout = 10000): Promise<Locator> {
    const locator = this.page.locator(selector)
    await locator.waitFor({ state: 'visible', timeout })
    return locator
  }

  /**
   * 等待元素消失
   */
  async waitForElementHidden(selector: string, timeout = 10000): Promise<void> {
    await this.page.locator(selector).waitFor({ state: 'hidden', timeout })
  }

  /**
   * 获取元素文本
   */
  async getText(selector: string): Promise<string> {
    return await this.page.locator(selector).textContent() || ''
  }

  /**
   * 检查页面是否包含文本
   */
  async hasText(text: string): Promise<boolean> {
    return await this.page.locator(`text=${text}`).count() > 0
  }
}
