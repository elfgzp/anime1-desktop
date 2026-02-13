const { contextBridge, ipcRenderer } = require('electron');

// Expose API to renderer process using contextBridge
contextBridge.exposeInMainWorld('electronAPI', {
  // Anime API
  getAnimeList: (params) => ipcRenderer.invoke('anime:list', params),
  getAnimeDetail: (params) => ipcRenderer.invoke('anime:detail', params),
  getEpisodes: (params) => ipcRenderer.invoke('anime:episodes', params),
  searchAnime: (params) => ipcRenderer.invoke('anime:search', params),
  getAnimeCover: (params) => ipcRenderer.invoke('anime:getCover', params),
  getBangumiInfo: (params) => ipcRenderer.invoke('anime:getBangumiInfo', params),

  // Favorite API
  getFavorites: () => ipcRenderer.invoke('favorite:list'),
  addFavorite: (params) => ipcRenderer.invoke('favorite:add', params),
  removeFavorite: (params) => ipcRenderer.invoke('favorite:remove', params),

  // Settings API
  getSettings: (params) => ipcRenderer.invoke('settings:get', params),
  setSettings: (params) => ipcRenderer.invoke('settings:set', params),

  // Playback History API
  updatePlayback: (params) => ipcRenderer.invoke('playback:update', params),
  getPlaybackHistory: (params) => ipcRenderer.invoke('playback:list', params),
  getEpisodeProgress: (params) => ipcRenderer.invoke('playback:episode', params),

  // Video Proxy API
  getVideoInfo: (params) => ipcRenderer.invoke('video:getInfo', params),

  // Cache API
  getCacheInfo: () => ipcRenderer.invoke('cache:info'),
  clearCache: (params) => ipcRenderer.invoke('cache:clear', params),

  // Updater API
  checkForUpdates: () => ipcRenderer.invoke('updater:check'),
  downloadUpdate: () => ipcRenderer.invoke('updater:download'),
  installUpdate: () => ipcRenderer.invoke('updater:install'),
  getUpdaterStatus: () => ipcRenderer.invoke('updater:status'),

  // Updater event listeners
  onUpdaterChecking: (callback) => ipcRenderer.on('updater:checking', callback),
  onUpdaterAvailable: (callback) => ipcRenderer.on('updater:available', callback),
  onUpdaterNotAvailable: (callback) => ipcRenderer.on('updater:not-available', callback),
  onUpdaterProgress: (callback) => ipcRenderer.on('updater:progress', callback),
  onUpdaterDownloaded: (callback) => ipcRenderer.on('updater:downloaded', callback),
  onUpdaterError: (callback) => ipcRenderer.on('updater:error', callback),

  // Remove updater listeners
  removeUpdaterListeners: () => {
    ipcRenderer.removeAllListeners('updater:checking');
    ipcRenderer.removeAllListeners('updater:available');
    ipcRenderer.removeAllListeners('updater:not-available');
    ipcRenderer.removeAllListeners('updater:progress');
    ipcRenderer.removeAllListeners('updater:downloaded');
    ipcRenderer.removeAllListeners('updater:error');
  },

  // Shell API
  openPath: (params) => ipcRenderer.invoke('shell:openPath', params),
  openExternal: (params) => ipcRenderer.invoke('shell:openExternal', params),
  openLogsFolder: () => ipcRenderer.invoke('shell:openLogsFolder'),

  // Window API
  getWindowState: () => ipcRenderer.invoke('window:getState'),
  saveWindowState: (params) => ipcRenderer.invoke('window:saveState', params),

  // App API
  getAppInfo: () => ipcRenderer.invoke('app:getInfo'),

  // Auto Download API
  getAutoDownloadConfig: () => ipcRenderer.invoke('autoDownload:getConfig'),
  updateAutoDownloadConfig: (config) => ipcRenderer.invoke('autoDownload:updateConfig', config),
  getAutoDownloadHistory: (params) => ipcRenderer.invoke('autoDownload:getHistory', params),
  getAutoDownloadActiveDownloads: () => ipcRenderer.invoke('autoDownload:getActiveDownloads'),
  startAutoDownload: (params) => ipcRenderer.invoke('autoDownload:startDownload', params),
  cancelAutoDownload: (params) => ipcRenderer.invoke('autoDownload:cancelDownload', params),
  deleteAutoDownload: (params) => ipcRenderer.invoke('autoDownload:deleteDownload', params),
  getAutoDownloadStatus: () => ipcRenderer.invoke('autoDownload:getStatus'),
  previewAutoDownloadFilter: (params) => ipcRenderer.invoke('autoDownload:previewFilter', params),
  getAutoDownloadProgress: (params) => ipcRenderer.invoke('autoDownload:getProgress', params),
  getAllAutoDownloads: () => ipcRenderer.invoke('autoDownload:getAllDownloads'),
  clearCompletedAutoDownloads: () => ipcRenderer.invoke('autoDownload:clearCompleted'),
  
  // Auto Download Events
  onAutoDownloadEvent: (callback) => {
    const channels = [
      'auto-download:download-started',
      'auto-download:download-progress',
      'auto-download:download-completed',
      'auto-download:download-error',
      'auto-download:download-cancelled',
    ];
    channels.forEach(channel => {
      ipcRenderer.on(channel, (event, data) => callback(channel, data));
    });
  },
  
  // Performance API
  recordPerformance: (data) => ipcRenderer.invoke('performance:record', data),
  batchRecordPerformance: (items) => ipcRenderer.invoke('performance:batchRecord', items),
  getPerformanceStats: () => ipcRenderer.invoke('performance:getStats'),
  getRecentTraces: (options) => ipcRenderer.invoke('performance:getRecentTraces', options),
  getTrace: (traceId) => ipcRenderer.invoke('performance:getTrace', traceId),
  clearPerformanceData: () => ipcRenderer.invoke('performance:clearAll'),
  
  // Logs API
  getLogs: (options) => ipcRenderer.invoke('logs:get', options),
  getLogStats: () => ipcRenderer.invoke('logs:getStats'),
  clearLogs: () => ipcRenderer.invoke('logs:clear'),
  exportLogs: (exportPath) => ipcRenderer.invoke('logs:export', exportPath),
  getLogFileInfo: () => ipcRenderer.invoke('logs:getFileInfo'),
});

console.log('[Preload] electronAPI exposed successfully via contextBridge');
