/**
 * 设置相关类型定义
 * 
 * 对应原项目: src/config.py, src/constants/settings.py
 */

// ==========================================
// 主题设置
// ==========================================

/** 主题模式 */
export type ThemeMode = 'light' | 'dark' | 'system'

/** 主题设置 */
export interface ThemeSettings {
  mode: ThemeMode
}

// ==========================================
// 窗口设置
// ==========================================

/** 窗口状态 */
export interface WindowSettings {
  width: number
  height: number
  x?: number
  y?: number
  maximized: boolean
}

// ==========================================
// 下载设置
// ==========================================

/** 自动下载过滤条件 */
export interface AutoDownloadFilters {
  /** 年份过滤，如 ['2024', '2025'] */
  years: string[]
  /** 季节过滤，如 ['冬', '春', '夏', '秋'] */
  seasons: string[]
}

/** 下载设置 */
export interface DownloadSettings {
  /** 默认下载路径 */
  downloadPath: string
  /** 是否启用自动下载 */
  autoDownloadEnabled: boolean
  /** 自动下载过滤条件 */
  filters: AutoDownloadFilters
  /** 最大同时下载数 */
  maxConcurrentDownloads: number
}

// ==========================================
// 播放设置
// ==========================================

/** 播放设置 */
export interface PlaybackSettings {
  /** 自动播放下一集 */
  autoPlayNext: boolean
  /** 记住播放位置 */
  rememberPlaybackPosition: boolean
  /** 默认音量 0-1 */
  defaultVolume: number
  /** 播放器默认清晰度 */
  defaultQuality?: string
}

// ==========================================
// 更新设置
// ==========================================

/** 更新通道 */
export type UpdateChannel = 'stable' | 'test'

/** 更新设置 */
export interface UpdateSettings {
  /** 更新通道 */
  channel: UpdateChannel
  /** 自动检查更新 */
  autoCheck: boolean
}

// ==========================================
// 完整应用设置
// ==========================================

/**
 * 完整的应用设置
 * 对应: src/config.py 中的所有配置项
 */
export interface AppSettings {
  // 主题
  theme: ThemeMode
  
  // 窗口
  window: WindowSettings
  
  // 下载
  download: DownloadSettings
  
  // 播放
  playback: PlaybackSettings
  
  // 更新
  update: UpdateSettings
}

/**
 * 设置键名枚举
 * 用于 settings:get 和 settings:set 的 key 参数
 */
export enum SettingKey {
  THEME = 'theme',
  WINDOW_STATE = 'windowState',
  DOWNLOAD_PATH = 'downloadPath',
  AUTO_DOWNLOAD_ENABLED = 'autoDownloadEnabled',
  AUTO_DOWNLOAD_FILTERS = 'autoDownloadFilters',
  AUTO_PLAY_NEXT = 'autoPlayNext',
  REMEMBER_PLAYBACK_POSITION = 'rememberPlaybackPosition',
  DEFAULT_VOLUME = 'defaultVolume',
  UPDATE_CHANNEL = 'updateChannel',
  AUTO_CHECK_UPDATES = 'autoCheckUpdates'
}

// ==========================================
// 默认值
// ==========================================

/** 默认窗口设置 */
export const DEFAULT_WINDOW_SETTINGS: WindowSettings = {
  width: 1280,
  height: 800,
  maximized: false
}

/** 默认下载设置 */
export const DEFAULT_DOWNLOAD_SETTINGS: DownloadSettings = {
  downloadPath: '',
  autoDownloadEnabled: false,
  filters: {
    years: [],
    seasons: []
  },
  maxConcurrentDownloads: 3
}

/** 默认播放设置 */
export const DEFAULT_PLAYBACK_SETTINGS: PlaybackSettings = {
  autoPlayNext: true,
  rememberPlaybackPosition: true,
  defaultVolume: 1
}

/** 默认更新设置 */
export const DEFAULT_UPDATE_SETTINGS: UpdateSettings = {
  channel: 'stable',
  autoCheck: true
}

/** 完整默认设置 */
export const DEFAULT_APP_SETTINGS: AppSettings = {
  theme: 'system',
  window: DEFAULT_WINDOW_SETTINGS,
  download: DEFAULT_DOWNLOAD_SETTINGS,
  playback: DEFAULT_PLAYBACK_SETTINGS,
  update: DEFAULT_UPDATE_SETTINGS
}
