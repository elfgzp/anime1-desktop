/**
 * Test data fixtures for E2E tests
 */

export const TEST_ANIME = {
  // Known anime titles for search tests
  searchKeywords: [
    '鬼灭',
    '进击',
    '间谍',
    '咒术',
  ],
  
  // Expected anime that should exist in the database
  knownAnime: {
    title: '鬼灭之刃',
    year: '2019',
    season: '春季',
  },
};

export const TEST_USER = {
  preferences: {
    theme: 'dark',
    sidebarCollapsed: false,
  },
};

export const TEST_TIMEOUTS = {
  short: 5000,
  medium: 10000,
  long: 30000,
  videoLoad: 60000,
};

export const SELECTORS = {
  // Home page
  home: {
    container: '.home-container',
    searchInput: '.search-input input',
    searchButton: '.search-button',
    animeGrid: '.anime-grid',
    animeCard: '.anime-card',
    pagination: '.el-pagination',
  },
  
  // Detail page
  detail: {
    container: '.detail-container',
    title: '.anime-title',
    cover: '.anime-cover img',
    episodeList: '.episode-list',
    episodeItem: '.episode-item',
    favoriteButton: '.favorite-button',
    playButton: '.play-button',
  },
  
  // Video player
  video: {
    container: '.video-player-wrapper',
    videojs: '.video-js',
    playButton: '.vjs-play-control',
    pauseButton: '.vjs-play-control.vjs-paused',
  },
  
  // Sidebar
  sidebar: {
    container: '.sidebar',
    menuItems: '.el-menu-item',
    home: '.sidebar-menu .el-menu-item:nth-child(1)',
    favorites: '.sidebar-menu .el-menu-item:nth-child(2)',
    history: '.sidebar-menu .el-menu-item:nth-child(3)',
    settings: '.sidebar-menu .el-menu-item:nth-child(4)',
  },
  
  // Settings
  settings: {
    container: '.settings-container',
    themeSelect: '.theme-selector .el-select',
    cacheClearButton: '.clear-cache-button',
    updateCheckButton: '.check-update-button',
  },
  
  // Favorites
  favorites: {
    container: '.favorites-container',
    emptyState: '.empty-state',
    animeList: '.favorites-list',
  },
  
  // Common
  loading: '.el-loading-mask',
  skeleton: '.el-skeleton',
  toast: '.el-message',
  dialog: '.el-dialog',
};
