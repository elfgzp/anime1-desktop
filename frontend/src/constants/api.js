/**
 * API 端点常量
 */

// API 基础路径
export const API_BASE = '/api'
export const PROXY_BASE = '/proxy'

// 番剧相关 API
export const API_ENDPOINTS = {
  ANIME: {
    BASE: '/anime',
    LIST: '/anime',
    SEARCH: '/anime/search',
    COVERS: '/anime/covers',
    EPISODES: (id) => `/anime/${id}/episodes`,
    BANGUMI: (id) => `/anime/${id}/bangumi`
  },
  
  // 收藏相关 API
  FAVORITE: {
    BASE: '/favorite',
    ADD: '/favorite/add',
    REMOVE: '/favorite/remove',
    LIST: '/favorite/list',
    CHECK: '/favorite/check',
    IS_FAVORITE: '/favorite/is_favorite',
    BATCH_STATUS: '/favorite/batch_status'
  },
  
  // 设置相关 API
  SETTINGS: {
    BASE: '/settings',
    THEME: '/settings/theme',
    ABOUT: '/settings/about',
    CHECK_UPDATE: '/settings/check_update',
    LOGS_OPEN: '/settings/logs/open',
    CACHE_INFO: '/settings/cache',
    CACHE_CLEAR: '/settings/cache/clear'
  },
  
  // 更新相关 API
  UPDATE: {
    BASE: '/update',
    CHECK: '/update/check',
    INFO: '/update/info'
  },
  
  // 代理相关 API
  PROXY: {
    EPISODE_API: '/proxy/episode-api',
    VIDEO_STREAM: '/proxy/video-stream',
    VIDEO_URL: '/proxy/video-url',
    VIDEO: '/proxy/video',
    PLAYER: '/proxy/player',
    HLS: '/proxy/hls'
  },

  // 播放历史相关 API
  PLAYBACK: {
    BASE: '/playback',
    UPDATE: '/playback/update',
    LIST: '/playback/list',
    EPISODE: '/playback/episode',
    LATEST: '/playback/latest',
    BATCH: '/playback/batch'
  }
}

// 请求参数名
export const REQUEST_PARAMS = {
  PAGE: 'page',
  KEYWORD: 'q',
  ANIME_ID: 'anime_id',
  IDS: 'ids',
  URL: 'url',
  COOKIES: 'cookies',
  THEME: 'theme'
}

// 响应字段名
export const RESPONSE_FIELDS = {
  SUCCESS: 'success',
  ERROR: 'error',
  DATA: 'data',
  MESSAGE: 'message',
  HAS_UPDATE: 'has_update',
  HAS_UPDATES: 'has_updates',
  CURRENT_VERSION: 'current_version',
  LATEST_VERSION: 'latest_version',
  IS_PRERELEASE: 'is_prerelease',
  RELEASE_NOTES: 'release_notes',
  DOWNLOAD_URL: 'download_url',
  ANIME_LIST: 'anime_list',
  CURRENT_PAGE: 'current_page',
  TOTAL_PAGES: 'total_pages',
  EPISODES: 'episodes',
  ANIME: 'anime',
  TITLE: 'title',
  COVER_URL: 'cover_url',
  YEAR: 'year',
  SEASON: 'season',
  SUBTITLE_GROUP: 'subtitle_group',
  EPISODE: 'episode',
  IS_FAVORITE: 'is_favorite',
  URL: 'url'
}

// 路由路径
export const ROUTES = {
  HOME: '/',
  FAVORITES: '/favorites',
  SETTINGS: '/settings',
  PLAYBACK: '/playback',
  ANIME_DETAIL: (id) => `/anime/${id}`
}

// 主题值
export const THEME = {
  DARK: 'dark',
  LIGHT: 'light',
  SYSTEM: 'system'
}

// 成人内容标记
export const ADULT_CONTENT = {
  MARKER: '🔞',
  DOMAIN: 'anime1.pw'
}

// UI 文本
export const UI_TEXT = {
  LOADING: '加载中...',
  LOADING_VIDEO: '正在加载视频...',
  SEARCHING: '搜索中...',
  NO_DATA: '暂无番剧数据',
  NO_FAVORITES: '暂无追番',
  ADD_FAVORITE: '追番',
  REMOVE_FAVORITE: '取消追番',
  FAVORITE_ADDED: '已添加追番',
  FAVORITE_REMOVED: '已取消追番',
  CLICK_TO_PLAY: '点击播放按钮开始播放',
  NO_EPISODES: '暂无剧集更新',
  WAIT_FOR_UPDATE: '请耐心等待番剧更新',
  THEME_UPDATED: '主题已更新',
  SEARCH_KEYWORD_REQUIRED: '请输入搜索关键词'
}

// 错误消息
export const ERROR_MESSAGES = {
  LOAD_FAILED: '加载失败',
  PLAY_FAILED: '播放失败',
  NO_VIDEO: '无法获取视频',
  NETWORK_ERROR: '网络错误，请稍后重试',
  UNKNOWN_ERROR: '未知错误',
  OPERATION_FAILED: '操作失败，请稍后重试',
  CHECK_UPDATE_FAILED: '检查更新失败'
}
