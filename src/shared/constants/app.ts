/**
 * 应用常量定义
 * 
 * 对应原项目: src/constants/app.py, src/config.py
 */

// ==========================================
// 应用信息
// ==========================================

export const APP_NAME = 'Anime1 Desktop'
export const APP_VERSION = '2.0.0'
export const APP_DESCRIPTION = 'Anime1 桌面客户端 - Electron 重构版'

// ==========================================
// 平台标识
// ==========================================

export const PLATFORM = {
  WIN32: 'win32',
  DARWIN: 'darwin',
  LINUX: 'linux'
} as const

// ==========================================
// 窗口配置
// ==========================================

export const WINDOW_CONFIG = {
  DEFAULT_WIDTH: 1280,
  DEFAULT_HEIGHT: 800,
  MIN_WIDTH: 900,
  MIN_HEIGHT: 600,
  TITLE_BAR_STYLE: 'hiddenInset' as const
}

// ==========================================
// 实例锁配置
// ==========================================

export const LOCK_CONFIG = {
  FILE_NAME: 'instance.lock',
  UPDATE_INTERVAL: 10000, // 10 seconds
  TIMEOUT: 30000 // 30 seconds
}

// ==========================================
// 下载配置
// ==========================================

export const DOWNLOAD_CONFIG = {
  CHUNK_SIZE: 8192,
  TIMEOUT: 300000, // 5 minutes
  MAX_CONCURRENT: 3,
  RETRY_ATTEMPTS: 3
}

// ==========================================
// 更新配置
// ==========================================

export const UPDATE_CONFIG = {
  GITHUB_OWNER: 'elfgzp',
  GITHUB_REPO: 'anime1-desktop',
  DEFAULT_CHANNEL: 'stable' as const,
  CHECK_INTERVAL: 24 * 60 * 60 * 1000 // 24 hours
}

// ==========================================
// 缓存配置
// ==========================================

export const CACHE_CONFIG = {
  REFRESH_INTERVAL: 300000, // 5 minutes
  LIST_TTL: 600000, // 10 minutes
  COVER_EXPIRY: 7 * 24 * 60 * 60 * 1000 // 7 days
}

// ==========================================
// 分页配置
// ==========================================

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 24,
  MAX_PAGE_SIZE: 100
}

// ==========================================
// IPC 频道常量
// ==========================================

export const IPC_CHANNELS = {
  // 窗口
  WINDOW: {
    MINIMIZE: 'window:minimize',
    MAXIMIZE: 'window:maximize',
    CLOSE: 'window:close',
    TOGGLE_FULLSCREEN: 'window:toggleFullscreen',
    GET_STATE: 'window:getState'
  },
  
  // 番剧
  ANIME: {
    LIST: 'anime:list',
    DETAIL: 'anime:detail',
    EPISODES: 'anime:episodes',
    SEARCH: 'anime:search',
    BANGUMI: 'anime:bangumi',
    CACHE_STATUS: 'anime:cache:status',
    CACHE_REFRESH: 'anime:cache:refresh'
  },
  
  // 收藏
  FAVORITE: {
    LIST: 'favorite:list',
    ADD: 'favorite:add',
    REMOVE: 'favorite:remove',
    CHECK: 'favorite:check'
  },
  
  // 历史
  HISTORY: {
    LIST: 'history:list',
    ADD: 'history:add',
    CLEAR: 'history:clear'
  },
  
  // 设置
  SETTINGS: {
    GET: 'settings:get',
    SET: 'settings:set',
    GET_ALL: 'settings:getAll'
  },
  
  // 下载
  DOWNLOAD: {
    LIST: 'download:list',
    ADD: 'download:add',
    PAUSE: 'download:pause',
    RESUME: 'download:resume',
    CANCEL: 'download:cancel',
    REMOVE: 'download:remove',
    PROGRESS: 'download:progress'
  },
  
  // 系统
  SYSTEM: {
    SHOW_ITEM_IN_FOLDER: 'system:showItemInFolder',
    OPEN_EXTERNAL: 'system:openExternal'
  },
  
  // 更新
  UPDATE: {
    CHECK: 'update:check',
    DOWNLOAD: 'update:download',
    INSTALL: 'update:install',
    AVAILABLE: 'update:available',
    PROGRESS: 'update:progress',
    DOWNLOADED: 'update:downloaded'
  }
} as const
