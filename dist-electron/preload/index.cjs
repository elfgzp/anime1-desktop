/**
 * Preload 脚本 - CommonJS 格式
 * 
 * ⚠️⚠️⚠️ 警告 ⚠️⚠️⚠️
 * 这是唯一的 preload 文件！不要创建 index.ts 或其他重复的 preload 文件！
 * 
 * 构建流程:
 * 1. vite 构建时会直接复制此文件到 dist-electron/preload/index.cjs
 * 2. 不会进行任何编译或类型检查
 * 3. 所有 API 类型定义在 src/shared/types/api.ts 中
 * 
 * 如需修改 preload API:
 * 1. 修改此文件添加/删除 API
 * 2. 同时在 validChannels 数组中添加/删除 IPC 频道
 * 3. 在 src/shared/types/api.ts 中更新类型定义
 * 4. 在 src/main/ipc/index.ts 中添加/删除 IPC 处理程序
 * 
 * 职责: 安全地暴露主进程 API 到渲染进程
 */

const { contextBridge, ipcRenderer } = require('electron')

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
  'anime:listWithProgress',
  'anime:detail',
  'anime:episodes',
  'anime:search',
  'anime:searchWithProgress',
  'anime:bangumi',
  'anime:video',
  'anime:video:proxy',
  'anime:cache:status',
  'anime:cache:refresh',
  
  // 收藏
  'favorite:list',
  'favorite:batchStatus',
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

// 安全的 IPC 调用
const invoke = async (channel, ...args) => {
  if (validChannels.includes(channel)) {
    return ipcRenderer.invoke(channel, ...args)
  }
  throw new Error(`Invalid channel: ${channel}`)
}

// 事件监听
const on = (channel, callback) => {
  if (validChannels.includes(channel)) {
    ipcRenderer.on(channel, (_, ...args) => callback(...args))
  }
}

// 暴露 API
const api = {
  window: {
    minimize: () => invoke('window:minimize'),
    maximize: () => invoke('window:maximize'),
    close: () => invoke('window:close'),
    toggleFullscreen: () => invoke('window:toggleFullscreen'),
    getState: () => invoke('window:getState')
  },
  
  anime: {
    getList: (params) => invoke('anime:list', params),
    getListWithProgress: (params) => invoke('anime:listWithProgress', params),
    getDetail: (params) => invoke('anime:detail', params),
    getEpisodes: (params) => invoke('anime:episodes', params),
    search: (params) => invoke('anime:search', params),
    searchWithProgress: (params) => invoke('anime:searchWithProgress', params),
    getBangumiInfo: (params) => invoke('anime:bangumi', params),
    extractVideo: (params) => invoke('anime:video', params),
    getVideoProxyUrl: (params) => invoke('anime:video:proxy', params),
    getCacheStatus: () => invoke('anime:cache:status'),
    refreshCache: () => invoke('anime:cache:refresh')
  },
  
  favorite: {
    getList: () => invoke('favorite:list'),
    batchStatus: (params) => invoke('favorite:batchStatus', params),
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
