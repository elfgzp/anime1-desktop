/**
 * 设置页面对象
 * 
 * 对应 views/Settings.vue
 */
import { BasePage } from './base-page'
import type { Page } from '@playwright/test'

export class SettingsPage extends BasePage {
  readonly selectors = {
    title: 'h1',
    downloadPath: '[data-testid="download-path"]',
    autoUpdate: '[data-testid="auto-update"]',
    themeSelect: '[data-testid="theme-select"]',
    clearCacheButton: '[data-testid="clear-cache"]',
    aboutSection: '[data-testid="about"]',
    version: '[data-testid="version"]',
    checkUpdateButton: '[data-testid="check-update"]',
    saveButton: '[data-testid="save-settings"]',
  }

  constructor(page: Page) {
    super(page)
  }

  /**
   * 导航到设置页
   */
  async goto(): Promise<void> {
    await this.page.goto('/settings')
    await this.waitForLoaded()
  }

  /**
   * 获取版本号
   */
  async getVersion(): Promise<string> {
    return await this.getText(this.selectors.version)
  }

  /**
   * 设置下载路径
   */
  async setDownloadPath(path: string): Promise<void> {
    await this.safeFill(this.selectors.downloadPath, path)
  }

  /**
   * 切换自动更新
   */
  async toggleAutoUpdate(enabled: boolean): Promise<void> {
    const checkbox = this.page.locator(this.selectors.autoUpdate)
    const isChecked = await checkbox.isChecked()
    if (isChecked !== enabled) {
      await checkbox.click()
    }
  }

  /**
   * 选择主题
   */
  async selectTheme(theme: 'light' | 'dark' | 'system'): Promise<void> {
    await this.page.locator(this.selectors.themeSelect).click()
    await this.page.locator(`.el-select-dropdown__item:has-text("${theme}")`).click()
  }

  /**
   * 点击清理缓存
   */
  async clearCache(): Promise<void> {
    await this.safeClick(this.selectors.clearCacheButton)
    // 等待确认对话框
    await this.page.locator('.el-message-box__btns .el-button--primary').click()
  }

  /**
   * 点击检查更新
   */
  async checkUpdate(): Promise<void> {
    await this.safeClick(this.selectors.checkUpdateButton)
  }

  /**
   * 保存设置
   */
  async save(): Promise<void> {
    await this.safeClick(this.selectors.saveButton)
  }

  /**
   * 获取设置值
   */
  async getSetting(key: string): Promise<string> {
    // 通过 IPC 调用获取设置
    return await this.page.evaluate(async (k) => {
      const result = await window.api.settings.get({ key: k })
      return result.success ? result.data : ''
    }, key)
  }
}
