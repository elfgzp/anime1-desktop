/**
 * 运行时配置管理
 * 
 * 对应原项目: src/config.py
 * 使用 electron-store 替代 Python 的常量/配置
 */

import Store from 'electron-store'
import { app } from 'electron'
import { join } from 'path'
import type { AppSettings } from '@shared/types'
import { DEFAULT_APP_SETTINGS } from '@shared/types'
import { 
  WINDOW_CONFIG,
  PAGINATION,
  HTTP_CONFIG,
  CACHE_CONFIG,
  DOWNLOAD_CONFIG
} from '@shared/constants'

// Store 实例
let store: Store<AppSettings> | null = null

/**
 * 获取配置存储实例
 */
export function getStore(): Store<AppSettings> {
  if (!store) {
    store = new Store<AppSettings>({
      name: 'anime1-config',
      defaults: DEFAULT_APP_SETTINGS,
      // 配置变更时自动持久化
      serialize: value => JSON.stringify(value, null, 2),
      deserialize: text => JSON.parse(text)
    })
  }
  return store
}

/**
 * 获取设置值
 */
export function getSetting<K extends keyof AppSettings>(key: K): AppSettings[K] {
  return getStore().get(key)
}

/**
 * 设置值
 */
export function setSetting<K extends keyof AppSettings>(key: K, value: AppSettings[K]): void {
  getStore().set(key, value)
}

/**
 * 获取所有设置
 */
export function getAllSettings(): AppSettings {
  return getStore().store
}

/**
 * 重置设置为默认值
 */
export function resetSettings(): void {
  getStore().clear()
}

// ==========================================
// 便捷访问方法
// ==========================================

export const config = {
  // 窗口
  get window() { return getSetting('window') },
  set window(value) { setSetting('window', value) },
  
  // 主题
  get theme() { return getSetting('theme') },
  set theme(value) { setSetting('theme', value) },
  
  // 下载
  get download() { return getSetting('download') },
  set download(value) { setSetting('download', value) },
  
  // 播放
  get playback() { return getSetting('playback') },
  set playback(value) { setSetting('playback', value) },
  
  // 更新
  get update() { return getSetting('update') },
  set update(value) { setSetting('update', value) }
}

// ==========================================
// 路径配置
// ==========================================

export const PATHS = {
  get USER_DATA() { return app.getPath('userData') },
  get DOWNLOADS() { return app.getPath('downloads') },
  get TEMP() { return app.getPath('temp') },
  
  // 数据库
  get DB_FILE() { return join(this.USER_DATA, 'anime1.db') },
  
  // 日志
  get LOG_DIR() { return join(this.USER_DATA, 'logs') },
  
  // 缓存
  get CACHE_DIR() { return join(this.USER_DATA, 'cache') },
  
  // 下载目录
  get DEFAULT_DOWNLOAD_DIR() { 
    return config.download.downloadPath || this.DOWNLOADS 
  }
} as const

// 导出常量
export {
  WINDOW_CONFIG,
  PAGINATION,
  HTTP_CONFIG,
  CACHE_CONFIG,
  DOWNLOAD_CONFIG,
  DEFAULT_APP_SETTINGS
}
