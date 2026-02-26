/**
 * 下载页面对象
 * 
 * 对应 views/Downloads.vue
 */
import { BasePage } from './base-page'
import type { Page } from '@playwright/test'

export class DownloadsPage extends BasePage {
  readonly selectors = {
    title: 'h1',
    empty: '.el-empty',
    downloadList: '.download-list',
    downloadItem: '.download-item',
    filename: '.filename',
    progress: '.progress',
    status: '.status',
    pauseButton: '.pause-btn',
    resumeButton: '.resume-btn',
    cancelButton: '.cancel-btn',
    openFolderButton: '.open-folder-btn',
  }

  constructor(page: Page) {
    super(page)
  }

  /**
   * 导航到下载页
   */
  async goto(): Promise<void> {
    await this.page.goto('/downloads')
    await this.waitForLoaded()
  }

  /**
   * 获取下载任务列表
   */
  async getDownloads(): Promise<Array<{
    filename: string
    progress: number
    status: string
  }>> {
    const items = this.page.locator(this.selectors.downloadItem)
    const count = await items.count()
    const downloads = []
    
    for (let i = 0; i < count; i++) {
      const item = items.nth(i)
      const filename = await item.locator(this.selectors.filename).textContent() || ''
      const progressText = await item.locator(this.selectors.progress).textContent() || '0%'
      const progress = parseInt(progressText.replace('%', ''), 10) || 0
      const status = await item.locator(this.selectors.status).textContent() || ''
      
      downloads.push({
        filename: filename.trim(),
        progress,
        status: status.trim(),
      })
    }
    
    return downloads
  }

  /**
   * 暂停下载任务
   */
  async pauseDownload(index: number): Promise<void> {
    await this.page.locator(this.selectors.downloadItem).nth(index)
      .locator(this.selectors.pauseButton).click()
  }

  /**
   * 恢复下载任务
   */
  async resumeDownload(index: number): Promise<void> {
    await this.page.locator(this.selectors.downloadItem).nth(index)
      .locator(this.selectors.resumeButton).click()
  }

  /**
   * 取消下载任务
   */
  async cancelDownload(index: number): Promise<void> {
    await this.page.locator(this.selectors.downloadItem).nth(index)
      .locator(this.selectors.cancelButton).click()
  }

  /**
   * 在文件夹中显示
   */
  async openInFolder(index: number): Promise<void> {
    await this.page.locator(this.selectors.downloadItem).nth(index)
      .locator(this.selectors.openFolderButton).click()
  }

  /**
   * 等待下载完成
   */
  async waitForDownloadComplete(index: number, timeout = 60000): Promise<void> {
    const startTime = Date.now()
    while (Date.now() - startTime < timeout) {
      const downloads = await this.getDownloads()
      if (downloads[index] && downloads[index].status === 'completed') {
        return
      }
      await this.page.waitForTimeout(500)
    }
    throw new Error(`Download did not complete within ${timeout}ms`)
  }
}
