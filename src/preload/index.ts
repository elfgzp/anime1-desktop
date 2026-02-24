/**
 * Preload 脚本
 * 
 * 职责: 安全地暴露主进程 API 到渲染进程
 */

import { contextBridge, ipcRenderer } from 'electron'

// IPC 频道白名单
const validChannels = [
  // 窗口
  'window:minimize',
  'window:maximize',
  'window:close',
  'window:toggleFullscreen',
  'window:getState',
  
  // 番剧
  'anime:list',
  'anime:detail',
  'anime:episodes',
  'anime:search',
  'anime:bangumi',
  'anime:video',
  'anime:cache:status',
  'anime:cache:refresh',
  
  // 收藏
  'favorite:list',
  'favorite:add',
  'favorite:remove',
  'favorite:check',
  
  // 播放历史
  'history:list',
  'history:save',
  'history:progress',
  'history:clear',
  
  // 设置
  'settings:get',
  'settings:set',
  'settings:getAll',
  
  // 下载
  'download:list',
  'download:add',
  'download:pause',
  'download:resume',
  'download:cancel',
  
  // 系统
  'system:showItemInFolder',
  'system:openExternal',
  
  // 更新
  'update:check',
  'update:download',
  'update:install'
]

// API 定义
export interface ElectronAPI {
  // 窗口控制
  window: {
    minimize: () => Promise<void>
    maximize: () => Promise<void>
    close: () => Promise<void>
    toggleFullscreen: () => Promise<void>
    getState: () => Promise<{ maximized: boolean; minimized: boolean; fullscreen: boolean; focused: boolean }>
  }
  
  // 番剧
  anime: {
    getList: (params: { page: number; pageSize?: number }) => Promise<any>
    getDetail: (params: { id: string }) => Promise<any>
    getEpisodes: (params: { id: string }) => Promise<any>
    search: (params: { keyword: string; page?: number }) => Promise<any>
    getBangumiInfo: (params: { id: string }) => Promise<any>
    extractVideo: (params: { episodeUrl: string }) => Promise<any>
    getCacheStatus: () => Promise<any>
    refreshCache: () => Promise<any>
  }
  
  // 收藏
  favorite: {
    getList: () => Promise<any>
    add: (params: { animeId: string; title: string; coverUrl?: string; detailUrl: string }) => Promise<any>
    remove: (params: { animeId: string }) => Promise<any>
    check: (params: { animeId: string }) => Promise<any>
  }
  
  // 播放历史
  history: {
    getList: (params?: { limit?: number }) => Promise<any>
    save: (params: {
      animeId: string
      animeTitle: string
      episodeId: string
      episodeNum: number
      positionSeconds: number
      totalSeconds: number
      coverUrl?: string
    }) => Promise<any>
    getProgress: (params: { animeId: string; episodeId: string }) => Promise<any>
    clear: () => Promise<any>
  }
  
  // 设置
  settings: {
    get: (params: { key: string }) => Promise<any>
    set: (params: { key: string; value: string }) => Promise<any>
    getAll: () => Promise<any>
  }
  
  // 下载
  download: {
    getList: () => Promise<any>
    add: (params: { url: string; filename: string }) => Promise<any>
    pause: (params: { taskId: string }) => Promise<any>
    resume: (params: { taskId: string }) => Promise<any>
    cancel: (params: { taskId: string }) => Promise<any>
    onProgress: (callback: (task: any) => void) => void
  }
  
  // 系统
  system: {
    showItemInFolder: (params: { path: string }) => Promise<void>
    openExternal: (params: { url: string }) => Promise<void>
  }
  
  // 更新
  update: {
    check: () => Promise<any>
    download: () => Promise<any>
    install: () => Promise<any>
    onAvailable: (callback: (info: any) => void) => void
    onProgress: (callback: (progress: number) => void) => void
    onDownloaded: (callback: () => void) => void
  }
}

// 安全的 IPC 调用
const invoke = async (channel: string, ...args: any[]): Promise<any> => {
  if (validChannels.includes(channel)) {
    return ipcRenderer.invoke(channel, ...args)
  }
  throw new Error(`Invalid channel: ${channel}`)
}

// 事件监听
const on = (channel: string, callback: (...args: any[]) => void): void => {
  if (validChannels.includes(channel)) {
    ipcRenderer.on(channel, (_, ...args) => callback(...args))
  }
}

// 暴露 API
const api: ElectronAPI = {
  window: {
    minimize: () => invoke('window:minimize'),
    maximize: () => invoke('window:maximize'),
    close: () => invoke('window:close'),
    toggleFullscreen: () => invoke('window:toggleFullscreen'),
    getState: () => invoke('window:getState')
  },
  
  anime: {
    getList: (params) => invoke('anime:list', params),
    getDetail: (params) => invoke('anime:detail', params),
    getEpisodes: (params) => invoke('anime:episodes', params),
    search: (params) => invoke('anime:search', params),
    getBangumiInfo: (params) => invoke('anime:bangumi', params),
    extractVideo: (params) => invoke('anime:video', params),
    getCacheStatus: () => invoke('anime:cache:status'),
    refreshCache: () => invoke('anime:cache:refresh')
  },
  
  favorite: {
    getList: () => invoke('favorite:list'),
    add: (params) => invoke('favorite:add', params),
    remove: (params) => invoke('favorite:remove', params),
    check: (params) => invoke('favorite:check', params)
  },
  
  history: {
    getList: (params) => invoke('history:list', params),
    save: (params) => invoke('history:save', params),
    getProgress: (params) => invoke('history:progress', params),
    clear: () => invoke('history:clear')
  },
  
  settings: {
    get: (params) => invoke('settings:get', params),
    set: (params) => invoke('settings:set', params),
    getAll: () => invoke('settings:getAll')
  },
  
  download: {
    getList: () => invoke('download:list'),
    add: (params) => invoke('download:add', params),
    pause: (params) => invoke('download:pause', params),
    resume: (params) => invoke('download:resume', params),
    cancel: (params) => invoke('download:cancel', params),
    onProgress: (callback) => on('download:progress', callback)
  },
  
  system: {
    showItemInFolder: (params) => invoke('system:showItemInFolder', params),
    openExternal: (params) => invoke('system:openExternal', params)
  },
  
  update: {
    check: () => invoke('update:check'),
    download: () => invoke('update:download'),
    install: () => invoke('update:install'),
    onAvailable: (callback) => on('update:available', callback),
    onProgress: (callback) => on('update:progress', callback),
    onDownloaded: (callback) => on('update:downloaded', callback)
  }
}

// 暴露到 window.api
console.log('[Preload] Starting to expose API...')
try {
  contextBridge.exposeInMainWorld('api', api)
  console.log('[Preload] API exposed successfully')
} catch (error) {
  console.error('[Preload] Failed to expose API:', error)
}

// 类型声明
declare global {
  interface Window {
    api: ElectronAPI
  }
}
