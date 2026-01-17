"""User-facing message constants for frontend and backend."""

from typing import Final

# ============================================================================
# Error Messages
# ============================================================================

ERROR_LOAD_FAILED: Final[str] = "加载失败"
ERROR_PLAY_FAILED: Final[str] = "播放失败"
ERROR_NO_VIDEO: Final[str] = "无法获取视频"
ERROR_NETWORK: Final[str] = "网络错误，请稍后重试"
ERROR_UNKNOWN: Final[str] = "未知错误"
ERROR_NOT_FOUND: Final[str] = "Not found"
ERROR_URL_REQUIRED: Final[str] = "URL is required"
ERROR_KEYWORD_REQUIRED: Final[str] = "Keyword is required"
ERROR_ANIME_NOT_FOUND: Final[str] = "Anime not found"
ERROR_INVALID_THEME: Final[str] = "Invalid theme"
ERROR_OPERATION_FAILED: Final[str] = "操作失败，请稍后重试"

# Backend-specific error messages
ERROR_INVALID_DOMAIN: Final[str] = "Only anime1.me URLs are allowed"
ERROR_MISSING_PARAMS: Final[str] = "Missing required parameters"
ERROR_INCOMPLETE_API_PARAMS: Final[str] = "Incomplete video API params"
ERROR_INVALID_PARAMS: Final[str] = "Invalid parameters"
ERROR_API_ERROR: Final[str] = "API returned error"
ERROR_NO_VIDEO_SOURCES: Final[str] = "No video sources found in API response"
ERROR_PLAYER_NOT_FOUND: Final[str] = "Video player not found"
ERROR_PLAYER_NOT_FOUND_ON_PAGE: Final[str] = "Video player not found on page"
ERROR_THEME_REQUIRED: Final[str] = "theme is required"
ERROR_INVALID_THEME_VALUE: Final[str] = "Invalid theme. Must be one of: dark, light, system"
ERROR_ANIME_ID_REQUIRED: Final[str] = "anime_id is required"
ERROR_ALREADY_IN_FAVORITES: Final[str] = "Already in favorites"
ERROR_NOT_IN_FAVORITES: Final[str] = "Not in favorites"
ERROR_FAILED_SET_THEME: Final[str] = "Failed to set theme"
ERROR_FAILED_GET_THEME: Final[str] = "Failed to get theme"
ERROR_FAILED_CHECK_UPDATE: Final[str] = "Failed to check for updates"
ERROR_UNKNOWN_BACKEND: Final[str] = "Unknown error"

# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_FAVORITE_ADDED: Final[str] = "已添加追番"
SUCCESS_FAVORITE_REMOVED: Final[str] = "已取消追番"
SUCCESS_THEME_UPDATED: Final[str] = "主题已更新"
SUCCESS_LATEST_VERSION: Final[str] = "已是最新版本"
SUCCESS_UPDATE_FOUND: Final[str] = "发现新版本"
SUCCESS_ADDED_TO_FAVORITES: Final[str] = "Added to favorites"
SUCCESS_REMOVED_FROM_FAVORITES: Final[str] = "Removed from favorites"

# ============================================================================
# Info Messages
# ============================================================================

INFO_CLICK_TO_PLAY: Final[str] = "点击播放按钮开始播放"
INFO_NO_EPISODES: Final[str] = "暂无剧集更新"
INFO_WAIT_FOR_UPDATE: Final[str] = "请耐心等待番剧更新"
INFO_NO_DATA: Final[str] = "暂无番剧数据"
INFO_NO_FAVORITES: Final[str] = "暂无追番"

# ============================================================================
# UI Labels
# ============================================================================

LABEL_LOADING: Final[str] = "加载中..."
LABEL_SEARCHING: Final[str] = "搜索中..."
LABEL_ADD_FAVORITE: Final[str] = "追番"
LABEL_REMOVE_FAVORITE: Final[str] = "取消追番"
LABEL_CHECKING: Final[str] = "检查中..."

# ============================================================================
# API Response Keys (Backend)
# ============================================================================

KEY_SUCCESS: Final[str] = "success"
KEY_ERROR: Final[str] = "error"
KEY_DATA: Final[str] = "data"
KEY_MESSAGE: Final[str] = "message"
KEY_URL: Final[str] = "url"
KEY_COOKIES: Final[str] = "cookies"
KEY_RAW: Final[str] = "raw"

# ============================================================================
# API Response Field Keys
# ============================================================================

KEY_ANIME_LIST: Final[str] = "anime_list"
KEY_CURRENT_PAGE: Final[str] = "current_page"
KEY_TOTAL_PAGES: Final[str] = "total_pages"
KEY_EPISODES: Final[str] = "episodes"
KEY_ANIME: Final[str] = "anime"
KEY_TOTAL_EPISODES: Final[str] = "total_episodes"
KEY_IS_FAVORITE: Final[str] = "is_favorite"
KEY_FAVORITES: Final[str] = "favorites"
KEY_HAS_UPDATE: Final[str] = "has_update"
KEY_CURRENT_VERSION: Final[str] = "current_version"
KEY_LATEST_VERSION: Final[str] = "latest_version"
KEY_IS_PRERELEASE: Final[str] = "is_prerelease"
KEY_RELEASE_NOTES: Final[str] = "release_notes"
KEY_DOWNLOAD_URL: Final[str] = "download_url"
KEY_ASSET_NAME: Final[str] = "asset_name"
KEY_DOWNLOAD_SIZE: Final[str] = "download_size"
KEY_PUBLISHED_AT: Final[str] = "published_at"
KEY_CHANNEL: Final[str] = "channel"
KEY_REPO_OWNER: Final[str] = "repo_owner"
KEY_REPO_NAME: Final[str] = "repo_name"
KEY_VERSION: Final[str] = "version"
KEY_REPOSITORY: Final[str] = "repository"
KEY_THEME: Final[str] = "theme"

# ============================================================================
# API Video Response Keys (from anime1.me API)
# ============================================================================

API_KEY_SUCCESS: Final[str] = "success"
API_KEY_FILE: Final[str] = "file"
API_KEY_STREAM: Final[str] = "stream"
API_KEY_VIDEO_SOURCES: Final[str] = "s"
API_KEY_SRC: Final[str] = "src"

# ============================================================================
# File and Directory Names
# ============================================================================

FILENAME_VERSION: Final[str] = "version.txt"
FILENAME_LOG: Final[str] = "anime1.log"
FILENAME_ANIME1_LOGO: Final[str] = "anime1-logo.png"

# ============================================================================
# Domain Names
# ============================================================================

DOMAIN_ANIME1_ME: Final[str] = "anime1.me"
DOMAIN_ANIME1_PW: Final[str] = "anime1.pw"

# ============================================================================
# Video API Constants
# ============================================================================

VIDEO_API_URL: Final[str] = "https://v.anime1.me/api"
VIDEO_API_PARAM_C: Final[str] = "c"
VIDEO_API_PARAM_E: Final[str] = "e"
VIDEO_API_PARAM_T: Final[str] = "t"
VIDEO_API_PARAM_P: Final[str] = "p"
VIDEO_API_PARAM_S: Final[str] = "s"
VIDEO_API_PARAM_D: Final[str] = "d"

# ============================================================================
# Content Type Constants
# ============================================================================

CONTENT_TYPE_JSON: Final[str] = "application/json"
CONTENT_TYPE_VIDEO_MP4: Final[str] = "video/mp4"
CONTENT_TYPE_APPLICATION_MPEGURL: Final[str] = "application/x-mpegURL"
CONTENT_TYPE_HTML: Final[str] = "text/html"

# ============================================================================
# CORS Headers
# ============================================================================

CORS_ALLOW_ORIGIN: Final[str] = "*"
CORS_ALLOW_METHODS: Final[str] = "GET, OPTIONS"
CORS_ALLOW_HEADERS: Final[str] = "Range"
CORS_X_FRAME_OPTIONS: Final[str] = "ALLOWALL"

# ============================================================================
# User Agent
# ============================================================================

DEFAULT_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ============================================================================
# Content Languages
# ============================================================================

ACCEPT_LANGUAGE: Final[str] = "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"

# ============================================================================
# Window Title
# ============================================================================

WINDOW_TITLE_BASE: Final[str] = "Anime1 桌面版"
WINDOW_TITLE_VERSION_PREFIX: Final[str] = "v"
WINDOW_TITLE_TEST_SUFFIX: Final[str] = "测试版"
WINDOW_TITLE_ERROR_SUFFIX: Final[str] = "启动失败"

# ============================================================================
# Static Resource URLs
# ============================================================================

STATIC_VIDEOJS_BUNDLE: Final[str] = "https://sta.anicdn.com/videojs.bundle.js?ver=8"
STATIC_JQUERY: Final[str] = "https://code.jquery.com/jquery-3.6.0.min.js"

# ============================================================================
# Default Values
# ============================================================================

DEFAULT_WEBVIEW_WIDTH: Final[int] = 1200
DEFAULT_WEBVIEW_HEIGHT: Final[int] = 800
DEFAULT_WEBVIEW_PORT: Final[int] = 7860
DEFAULT_ANIME_PAGE_SIZE: Final[int] = 20
MAX_BATCH_IDS: Final[int] = 100
