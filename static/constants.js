/* Application Constants */

// API Endpoints
const API_ENDPOINTS = {
    ANIME: '/api/anime',
    ANIME_SEARCH: '/api/anime/search',
    COVERS: '/api/anime/covers',
    UPDATE_CHECK: '/api/update/check',
    UPDATE_INFO: '/api/update/info',
    FAVORITE_ADD: '/api/favorite/add',
    FAVORITE_REMOVE: '/api/favorite/remove',
    FAVORITE_LIST: '/api/favorite/list',
    FAVORITE_CHECK: '/api/favorite/check',
    FAVORITE_IS_FAVORITE: '/api/favorite/is_favorite',
    SETTINGS_THEME: '/api/settings/theme',
    SETTINGS_CHECK_UPDATE: '/api/settings/check_update',
    SETTINGS_ABOUT: '/api/settings/about',
    PLAYBACK_UPDATE: '/api/playback/update',
    PLAYBACK_LIST: '/api/playback/list',
    PLAYBACK_EPISODE: '/api/playback/episode',
    PLAYBACK_LATEST: '/api/playback/latest',
    PLAYBACK_BATCH: '/api/playback/batch'
};

// Routes
const ROUTES = {
    HOME: '/',
    FAVORITES: '/favorites',
    SETTINGS: '/settings',
    ANIME_DETAIL: (id) => `/anime/${id}`
};

// Theme values
const THEME = {
    DARK: 'dark',
    LIGHT: 'light',
    SYSTEM: 'system'
};

// CSS Classes
const CSS_CLASSES = {
    HIDDEN: 'hidden',
    ACTIVE: 'active',
    LOADING: 'loading',
    HAS_UPDATE: 'has-update'
};

// UI Text
const UI_TEXT = {
    LOADING: '加载中...',
    SEARCHING: '搜索中...',
    NO_DATA: '暂无番剧数据',
    NO_FAVORITES: '暂无追番',
    ADD_FAVORITE: '追番',
    REMOVE_FAVORITE: '取消追番',
    PAGE_PREFIX: '第 ',
    PAGE_SUFFIX: ' 页'
};

// Menu items
const MENU_ITEMS = {
    LATEST: {
        id: 'latest',
        label: '最新番剧',
        route: ROUTES.HOME,
        icon: '📺'
    },
    FAVORITES: {
        id: 'favorites',
        label: '我的追番',
        route: ROUTES.FAVORITES,
        icon: '⭐'
    },
    SETTINGS: {
        id: 'settings',
        label: '设置',
        route: ROUTES.SETTINGS,
        icon: '⚙️'
    }
};

// Response keys
const RESPONSE_KEYS = {
    SUCCESS: 'success',
    ERROR: 'error',
    DATA: 'data',
    MESSAGE: 'message'
};
