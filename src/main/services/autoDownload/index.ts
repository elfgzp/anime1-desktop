/**
 * 自动下载服务
 * 
 * 对应原项目: src/services/auto_download_service.py
 * 职责: 自动下载配置管理、筛选、调度
 */

import { EventEmitter } from 'events'
import { join } from 'path'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import type {
  AutoDownloadConfig,
  DownloadFilter,
  DownloadRecord,
  AutoDownloadStatus
} from '@shared/types'
import { DownloadRecordStatus } from '@shared/types'
import { PATHS } from '../../config'

const CONFIG_FILE_NAME = 'auto_download_config.json'
const DOWNLOAD_HISTORY_FILE_NAME = 'auto_download_history.json'

/** 默认配置 */
const DEFAULT_CONFIG: AutoDownloadConfig = {
  enabled: false,
  downloadPath: '',
  checkIntervalHours: 24,
  maxConcurrentDownloads: 2,
  filters: {
    specificYears: [],
    seasons: [],
    includePatterns: [],
    excludePatterns: []
  },
  autoDownloadNew: true,
  autoDownloadFavorites: false
}

export class AutoDownloadService extends EventEmitter {
  private configPath: string
  private historyPath: string
  private config: AutoDownloadConfig | null = null
  private running = false
  private schedulerTimer: NodeJS.Timeout | null = null

  constructor() {
    super()
    this.configPath = join(PATHS.USER_DATA, CONFIG_FILE_NAME)
    this.historyPath = join(PATHS.USER_DATA, DOWNLOAD_HISTORY_FILE_NAME)
    this.ensureFilesExist()
  }

  /** 确保配置文件存在 */
  private ensureFilesExist(): void {
    if (!existsSync(this.configPath)) {
      this.saveConfig(DEFAULT_CONFIG)
    }
    if (!existsSync(this.historyPath)) {
      this.saveHistory([])
    }
  }

  /** 加载配置 */
  private loadConfig(): AutoDownloadConfig {
    try {
      if (existsSync(this.configPath)) {
        const data = readFileSync(this.configPath, 'utf-8')
        const parsed = JSON.parse(data)
        return { ...DEFAULT_CONFIG, ...parsed }
      }
    } catch (error) {
      console.error('[AutoDownload] Error loading config:', error)
    }
    return DEFAULT_CONFIG
  }

  /** 保存配置 */
  private saveConfig(config: AutoDownloadConfig): void {
    try {
      const dir = join(this.configPath, '..')
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true })
      }
      writeFileSync(this.configPath, JSON.stringify(config, null, 2), 'utf-8')
    } catch (error) {
      console.error('[AutoDownload] Error saving config:', error)
      throw error
    }
  }

  /** 加载历史记录 */
  private loadHistory(): DownloadRecord[] {
    try {
      if (existsSync(this.historyPath)) {
        const data = readFileSync(this.historyPath, 'utf-8')
        return JSON.parse(data)
      }
    } catch (error) {
      console.error('[AutoDownload] Error loading history:', error)
    }
    return []
  }

  /** 保存历史记录 */
  private saveHistory(history: DownloadRecord[]): void {
    try {
      const dir = join(this.historyPath, '..')
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true })
      }
      writeFileSync(this.historyPath, JSON.stringify(history, null, 2), 'utf-8')
    } catch (error) {
      console.error('[AutoDownload] Error saving history:', error)
      throw error
    }
  }

  /** 获取配置 */
  getConfig(): AutoDownloadConfig {
    if (!this.config) {
      this.config = this.loadConfig()
    }
    return this.config
  }

  /** 更新配置 */
  updateConfig(config: AutoDownloadConfig): boolean {
    try {
      this.saveConfig(config)
      this.config = config
      
      // 如果启用状态改变，重启/停止调度器
      if (config.enabled && !this.running) {
        this.startScheduler()
      } else if (!config.enabled && this.running) {
        this.stopScheduler()
      }
      
      this.emit('configUpdated', config)
      console.log('[AutoDownload] Config updated')
      return true
    } catch (error) {
      console.error('[AutoDownload] Failed to update config:', error)
      return false
    }
  }

  /** 获取下载路径 */
  getDownloadPath(): string {
    const config = this.getConfig()
    if (config.downloadPath && existsSync(config.downloadPath)) {
      return config.downloadPath
    }
    // 默认下载目录
    return PATHS.DEFAULT_DOWNLOAD_DIR
  }

  /** 获取下载历史 */
  getHistory(limit: number = 100, status?: DownloadRecordStatus): DownloadRecord[] {
    const history = this.loadHistory()
    let filtered = history
    if (status) {
      filtered = history.filter(r => r.status === status)
    }
    return filtered
      .sort((a, b) => b.createdAt - a.createdAt)
      .slice(0, limit)
  }

  /** 添加下载记录 */
  addDownloadRecord(record: DownloadRecord): void {
    const history = this.loadHistory()
    history.push(record)
    this.saveHistory(history)
    this.emit('recordAdded', record)
  }

  /** 更新下载记录 */
  updateDownloadRecord(record: DownloadRecord): void {
    const history = this.loadHistory()
    const index = history.findIndex(r => r.episodeId === record.episodeId)
    if (index !== -1) {
      history[index] = { ...history[index], ...record }
      this.saveHistory(history)
      this.emit('recordUpdated', history[index])
    }
  }

  /** 检查剧集是否已下载 */
  isEpisodeDownloaded(episodeId: string): boolean {
    const history = this.loadHistory()
    return history.some(r => 
      r.episodeId === episodeId && 
      (r.status === DownloadRecordStatus.COMPLETED || r.status === DownloadRecordStatus.DOWNLOADING)
    )
  }

  /** 筛选番剧 */
  filterAnime(animeList: any[]): any[] {
    const config = this.getConfig()
    return animeList.filter(anime => this.matchesFilter(anime, config.filters))
  }

  /** 检查番剧是否匹配筛选条件 */
  private matchesFilter(anime: any, filter: DownloadFilter): boolean {
    // 年份检查
    const yearStr = anime.year || ''
    if (yearStr) {
      const year = parseInt(yearStr, 10)
      if (!isNaN(year)) {
        if (filter.minYear !== undefined && year < filter.minYear) return false
        if (filter.maxYear !== undefined && year > filter.maxYear) return false
        if (filter.specificYears.length > 0 && !filter.specificYears.includes(year)) return false
      }
    }

    // 季度检查
    if (filter.seasons.length > 0) {
      const season = anime.season || ''
      if (season && !filter.seasons.includes(season)) return false
    }

    // 集数检查
    if (filter.minEpisodes !== undefined) {
      const episode = anime.episode || 0
      if (typeof episode === 'number' && episode < filter.minEpisodes) return false
    }

    // 标题正则检查
    const title = anime.title || ''
    if (filter.includePatterns.length > 0) {
      let matched = false
      for (const pattern of filter.includePatterns) {
        try {
          const regex = new RegExp(pattern, 'i')
          if (regex.test(title)) {
            matched = true
            break
          }
        } catch (e) {
          continue
        }
      }
      if (!matched) return false
    }

    if (filter.excludePatterns.length > 0) {
      for (const pattern of filter.excludePatterns) {
        try {
          const regex = new RegExp(pattern, 'i')
          if (regex.test(title)) return false
        } catch (e) {
          continue
        }
      }
    }

    return true
  }

  /** 启动调度器 */
  startScheduler(): void {
    if (this.running) {
      console.log('[AutoDownload] Scheduler already running')
      return
    }

    const config = this.getConfig()
    if (!config.enabled) {
      console.log('[AutoDownload] Disabled, not starting scheduler')
      return
    }

    this.running = true
    this.scheduleNextCheck()
    console.log('[AutoDownload] Scheduler started')
    this.emit('schedulerStarted')
  }

  /** 停止调度器 */
  stopScheduler(): void {
    if (!this.running) return

    if (this.schedulerTimer) {
      clearTimeout(this.schedulerTimer)
      this.schedulerTimer = null
    }
    this.running = false
    console.log('[AutoDownload] Scheduler stopped')
    this.emit('schedulerStopped')
  }

  /** 调度下次检查 */
  private scheduleNextCheck(): void {
    if (!this.running) return

    const config = this.getConfig()
    const intervalMs = config.checkIntervalHours * 60 * 60 * 1000

    this.schedulerTimer = setTimeout(() => {
      this.checkAndDownload()
      this.scheduleNextCheck()
    }, intervalMs)

    console.log(`[AutoDownload] Next check in ${config.checkIntervalHours} hours`)
  }

  /** 检查并下载 */
  private async checkAndDownload(): Promise<void> {
    if (!this.running) return

    console.log('[AutoDownload] Running auto download check...')
    this.emit('checkStarted')

    try {
      // 这里应该调用爬虫服务检查新剧集
      // 并触发下载
      // 暂时留空，需要在 IPC 层实现具体逻辑
      this.emit('checkCompleted', { checked: 0, downloaded: 0 })
    } catch (error) {
      console.error('[AutoDownload] Check error:', error)
      this.emit('checkError', error)
    }
  }

  /** 立即执行检查 */
  async runCheckNow(): Promise<{ checked: number; downloaded: number }> {
    console.log('[AutoDownload] Manual check triggered')
    this.emit('checkStarted')

    // 返回模拟结果，实际逻辑需要在 IPC 层实现
    const result = { checked: 0, downloaded: 0 }
    this.emit('checkCompleted', result)
    return result
  }

  /** 获取状态 */
  getStatus(): AutoDownloadStatus {
    const config = this.getConfig()
    const history = this.getHistory(10)
    const allHistory = this.getHistory(10000)

    const statusCounts = {
      pending: 0,
      downloading: 0,
      completed: 0,
      failed: 0,
      skipped: 0
    }

    for (const record of allHistory) {
      statusCounts[record.status]++
    }

    return {
      enabled: config.enabled,
      running: this.running,
      downloadPath: this.getDownloadPath(),
      checkIntervalHours: config.checkIntervalHours,
      filters: config.filters,
      recentDownloads: history,
      statusCounts
    }
  }

  /** 预览筛选结果 */
  previewFilter(animeList: any[], tempFilter?: DownloadFilter): {
    totalAnime: number
    matchedCount: number
    matchedAnime: any[]
  } {
    const config = this.getConfig()
    const filter = tempFilter || config.filters

    const filtered = animeList.filter(anime => this.matchesFilter(anime, filter))

    return {
      totalAnime: animeList.length,
      matchedCount: filtered.length,
      matchedAnime: filtered.slice(0, 50) // 限制预览数量
    }
  }
}

// 单例实例
let autoDownloadService: AutoDownloadService | null = null

export function getAutoDownloadService(): AutoDownloadService {
  if (!autoDownloadService) {
    autoDownloadService = new AutoDownloadService()
  }
  return autoDownloadService
}
