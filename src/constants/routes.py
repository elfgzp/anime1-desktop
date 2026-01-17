"""Route path constants for Flask routes."""

# API route prefixes
API_PREFIX = "/api"
PROXY_PREFIX = "/proxy"

# Page routes
ROUTE_HOME = "/"
ROUTE_FAVORITES = "/favorites"
ROUTE_SETTINGS = "/settings"
ROUTE_ANIME_DETAIL = "/anime/<anime_id>"

# API route paths
API_ANIME = f"{API_PREFIX}/anime"
API_ANIME_SEARCH = f"{API_PREFIX}/anime/search"
API_ANIME_COVERS = f"{API_PREFIX}/anime/covers"
API_ANIME_EPISODES = f"{API_PREFIX}/anime/<anime_id>/episodes"

API_FAVORITE_ADD = f"{API_PREFIX}/favorite/add"
API_FAVORITE_REMOVE = f"{API_PREFIX}/favorite/remove"
API_FAVORITE_LIST = f"{API_PREFIX}/favorite/list"
API_FAVORITE_CHECK = f"{API_PREFIX}/favorite/check"
API_FAVORITE_IS_FAVORITE = f"{API_PREFIX}/favorite/is_favorite"

API_SETTINGS_THEME = f"{API_PREFIX}/settings/theme"
API_SETTINGS_ABOUT = f"{API_PREFIX}/settings/about"
API_SETTINGS_CHECK_UPDATE = f"{API_PREFIX}/settings/check_update"

API_UPDATE_CHECK = f"{API_PREFIX}/update/check"
API_UPDATE_INFO = f"{API_PREFIX}/update/info"

# Proxy route paths
PROXY_EPISODE_API = f"{PROXY_PREFIX}/episode-api"
PROXY_VIDEO_STREAM = f"{PROXY_PREFIX}/video-stream"
PROXY_VIDEO_URL = f"{PROXY_PREFIX}/video-url"
PROXY_VIDEO = f"{PROXY_PREFIX}/video"
PROXY_PLAYER = f"{PROXY_PREFIX}/player"
PROXY_FULL = f"{PROXY_PREFIX}/full"
PROXY_EMBED = f"{PROXY_PREFIX}/embed"
