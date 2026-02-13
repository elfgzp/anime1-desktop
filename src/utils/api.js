// API layer using Electron IPC
// Adapts frontend API calls to use window.electronAPI

// Helper to call electron API
const callElectron = async (channel, data = {}) => {
  if (!window.electronAPI) {
    console.error('[API] window.electronAPI not available')
    throw new Error('electronAPI not available')
  }
  
  try {
    const result = await window.electronAPI[channel](data)
    console.log(`[API] ${channel} response:`, result)
    return result
  } catch (error) {
    console.error(`[API] ${channel} error:`, error)
    throw error
  }
}

// 番剧相关 API
export const animeAPI = {
  // 获取番剧列表
  getList: (page = 1, forceRefresh = false) => callElectron('getAnimeList', { page, forceRefresh }),

  // 搜索番剧
  search: (keyword, page = 1) => callElectron('searchAnime', { keyword, page }),

  // 获取番剧详情
  getDetail: (id, forceRefresh = false) => callElectron('getAnimeDetail', { id, forceRefresh }),

  // 获取番剧集数
  getEpisodes: (id) => callElectron('getEpisodes', { id }),

  // 获取封面（通过 Bangumi）
  getCover: (title) => callElectron('getAnimeCover', { title }),

  // 获取视频信息（通过代理）
  getVideoInfo: (url) => callElectron('getVideoInfo', { url }),

  // 获取 Bangumi 番剧信息
  getBangumiInfo: (id, title) => callElectron('getBangumiInfo', { id, title }),
}

// 收藏相关 API
export const favoriteAPI = {
  // 添加收藏
  add: (animeId) => callElectron('addFavorite', { animeId }),

  // 移除收藏
  remove: (animeId) => callElectron('removeFavorite', { animeId }),

  // 获取收藏列表
  getList: () => callElectron('getFavorites'),

  // 检查收藏状态
  isFavorite: async (animeId) => {
    const result = await callElectron('getFavorites')
    if (result.success && result.data) {
      return result.data.some(f => f.id === animeId)
    }
    return false
  },

  // 批量检查收藏状态 - 返回布尔数组
  batchStatus: async (ids) => {
    const result = await callElectron('getFavorites')
    const favoriteIds = result.success && result.data ? result.data.map(f => f.id) : []
    const idArray = typeof ids === 'string' ? ids.split(',') : (Array.isArray(ids) ? ids : [])
    const statusArray = idArray.map(id => favoriteIds.includes(id))
    
    // Return in the format expected by existing code
    return {
      success: true,
      data: statusArray
    }
  },

  // 检查收藏更新（TODO: implement in main process）
  checkUpdates: async () => {
    console.log('[API] checkUpdates not implemented yet')
    return { success: true, data: { has_updates: false, updates: [] } }
  },
}

// 设置相关 API
export const settingsAPI = {
  // 获取设置
  get: (key) => callElectron('getSettings', { key }),

  // 保存设置
  set: (key, value) => callElectron('setSettings', { key, value }),

  // 获取主题
  getTheme: () => callElectron('getSettings', { key: 'theme' }),

  // 保存主题
  saveTheme: (theme) => callElectron('setSettings', { key: 'theme', value: theme }),

  // 更新相关（using electron-updater）
  checkUpdate: async () => {
    return await callElectron('checkForUpdates')
  },
  getUpdateProgress: async () => {
    const status = await callElectron('getUpdaterStatus')
    return { success: true, data: status.data?.progress || { status: 'idle', percent: 0 } }
  },
  downloadUpdate: async () => {
    return await callElectron('downloadUpdate')
  },
  
  // 关于页面 - Match Python version format
  getAbout: async () => {
    const appInfo = await callElectron('getAppInfo')
    return { 
      success: true, 
      data: { 
        version: appInfo.data?.version || '0.1.0', 
        channel: appInfo.data?.channel || 'stable',
        repository: appInfo.data?.repository || 'https://github.com/elfgzp/anime1-desktop',
        repo_owner: appInfo.data?.repo_owner || 'elfgzp',
        repo_name: appInfo.data?.repo_name || 'anime1-desktop',
        // Additional Electron-specific info
        electron_version: appInfo.data?.electronVersion,
        chrome_version: appInfo.data?.chromeVersion,
        node_version: appInfo.data?.nodeVersion,
        platform: appInfo.data?.platform,
        arch: appInfo.data?.arch,
      } 
    }
  },
  
  // 日志文件夹 - 使用 Shell API
  openLogsFolder: async () => {
    return await callElectron('openLogsFolder')
  },
  
  // 缓存相关
  getCacheInfo: () => callElectron('getCacheInfo'),
  clearCache: (type = 'all') => callElectron('clearCache', { type }),
  
  // 播放列表缓存
  getPlaylistCacheStats: () => callElectron('getPlaylistCacheStats'),
  refreshPlaylistCache: () => callElectron('refreshPlaylistCache'),
  refreshAnimeDetailCache: (id) => callElectron('refreshAnimeDetailCache', { id }),
}

// 播放历史相关 API
export const playbackAPI = {
  // 更新播放进度
  update: (data) => callElectron('updatePlayback', data),

  // 获取播放历史列表
  getList: (limit = 50) => callElectron('getPlaybackHistory', { limit }),

  // 获取单集播放进度
  getEpisodeProgress: (animeId, episodeId) => callElectron('getEpisodeProgress', { animeId, episodeId }),

  // 批量获取播放进度（stub）
  batchProgress: async (ids) => {
    console.log('[API] batchProgress not implemented yet, ids:', ids)
    const progressMap = {}
    ids.split(',').forEach(id => {
      progressMap[id] = { currentTime: 0, duration: 0, completed: false }
    })
    return { success: true, data: progressMap }
  },
}

// 更新相关 API (using electron-updater)
export const updateAPI = {
  // Check for updates
  check: async () => {
    const result = await callElectron('checkForUpdates');
    return result;
  },

  // Get current updater status
  getStatus: async () => {
    const result = await callElectron('getUpdaterStatus');
    return result;
  },

  // Download update
  download: async () => {
    const result = await callElectron('downloadUpdate');
    return result;
  },

  // Install update
  install: async () => {
    const result = await callElectron('installUpdate');
    return result;
  },

  // Event listeners for update progress
  onChecking: (callback) => {
    if (window.electronAPI?.onUpdaterChecking) {
      window.electronAPI.onUpdaterChecking((event, data) => callback(data));
    }
  },

  onAvailable: (callback) => {
    if (window.electronAPI?.onUpdaterAvailable) {
      window.electronAPI.onUpdaterAvailable((event, data) => callback(data));
    }
  },

  onNotAvailable: (callback) => {
    if (window.electronAPI?.onUpdaterNotAvailable) {
      window.electronAPI.onUpdaterNotAvailable((event, data) => callback(data));
    }
  },

  onProgress: (callback) => {
    if (window.electronAPI?.onUpdaterProgress) {
      window.electronAPI.onUpdaterProgress((event, data) => callback(data));
    }
  },

  onDownloaded: (callback) => {
    if (window.electronAPI?.onUpdaterDownloaded) {
      window.electronAPI.onUpdaterDownloaded((event, data) => callback(data));
    }
  },

  onError: (callback) => {
    if (window.electronAPI?.onUpdaterError) {
      window.electronAPI.onUpdaterError((event, data) => callback(data));
    }
  },

  // Remove all listeners
  removeListeners: () => {
    if (window.electronAPI?.removeUpdaterListeners) {
      window.electronAPI.removeUpdaterListeners();
    }
  },
}

// Shell 相关 API
export const shellAPI = {
  // 打开本地路径
  openPath: (path) => callElectron('openPath', { path }),
  
  // 用外部浏览器打开 URL
  openExternal: (url) => callElectron('openExternal', { url }),
  
  // 打开日志文件夹
  openLogsFolder: () => callElectron('openLogsFolder'),
}

// 窗口相关 API
export const windowAPI = {
  // 获取窗口状态
  getState: () => callElectron('getWindowState'),
  
  // 保存窗口状态
  saveState: (state) => callElectron('saveWindowState', state),
}

// 应用相关 API
export const appAPI = {
  // 获取应用信息
  getInfo: () => callElectron('getAppInfo'),
}

// 性能追踪相关 API（stub）
// 性能追踪相关 API
export const performanceAPI = {
  // 记录性能数据
  record: (data) => callElectron('recordPerformance', data),
  
  // 批量记录性能数据
  batchRecord: (items) => callElectron('batchRecordPerformance', items),
  
  // 获取统计数据
  getStats: () => callElectron('getPerformanceStats'),
  
  // 获取最近追踪
  getRecentTraces: (options = {}) => callElectron('getRecentTraces', options),
  
  // 获取单个追踪详情
  getTrace: (traceId) => callElectron('getTrace', { traceId }),
  
  // 清除数据
  clearData: () => callElectron('clearPerformanceData'),
  clearAllData: () => callElectron('clearPerformanceData'),
}

// 自动下载相关 API
export const autoDownloadAPI = {
  // 获取配置
  getConfig: () => callElectron('getAutoDownloadConfig'),
  
  // 更新配置
  updateConfig: (config) => callElectron('updateAutoDownloadConfig', config),
  
  // 获取下载历史
  getHistory: (limit = 50, status = null) => callElectron('getAutoDownloadHistory', { limit, status }),
  
  // 获取正在下载的任务
  getActiveDownloads: () => callElectron('getAutoDownloadActiveDownloads'),
  
  // 开始下载
  startDownload: (anime, episode, videoUrl) => callElectron('startAutoDownload', { anime, episode, videoUrl }),
  
  // 取消下载
  cancelDownload: (downloadId) => callElectron('cancelAutoDownload', { downloadId }),
  
  // 删除下载记录
  deleteDownload: (downloadId) => callElectron('deleteAutoDownload', { downloadId }),
  
  // 获取服务状态
  getStatus: () => callElectron('getAutoDownloadStatus'),
  
  // 预览筛选结果
  previewFilter: (animeList) => callElectron('previewAutoDownloadFilter', { animeList }),
  
  // 获取下载进度
  getProgress: (episodeId) => callElectron('getAutoDownloadProgress', { episodeId }),
  
  // 获取所有下载（包括队列中的）
  getAllDownloads: () => callElectron('getAllAutoDownloads'),
  
  // 清除已完成的下载
  clearCompleted: () => callElectron('clearCompletedAutoDownloads'),
  
  // 注册下载事件监听
  onDownloadEvent: (callback) => {
    if (window.electronAPI?.onAutoDownloadEvent) {
      window.electronAPI.onAutoDownloadEvent(callback);
    }
  },
}

// 日志相关 API
export const logsAPI = {
  // 获取日志
  getLogs: (options = {}) => callElectron('getLogs', options),
  
  // 获取日志统计
  getLogStats: () => callElectron('getLogStats'),
  
  // 清除日志
  clearLogs: () => callElectron('clearLogs'),
  
  // 导出日志
  exportLogs: (exportPath) => callElectron('exportLogs', { exportPath }),
  
  // 获取日志文件信息
  getLogFileInfo: () => callElectron('getLogFileInfo'),
}

export default {
  anime: animeAPI,
  favorite: favoriteAPI,
  settings: settingsAPI,
  playback: playbackAPI,
  update: updateAPI,
  performance: performanceAPI,
  autoDownload: autoDownloadAPI,
  logs: logsAPI,
  shell: shellAPI,
  window: windowAPI,
  app: appAPI,
}
