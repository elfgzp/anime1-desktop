const { ipcRenderer } = require('electron');

// Expose API to renderer process
window.electronAPI = {
  // Anime API
  getAnimeList: (params) => ipcRenderer.invoke('anime:list', params),
  getAnimeDetail: (params) => ipcRenderer.invoke('anime:detail', params),
  getEpisodes: (params) => ipcRenderer.invoke('anime:episodes', params),
  searchAnime: (params) => ipcRenderer.invoke('anime:search', params),

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
};

console.log('[Preload] electronAPI exposed successfully');
