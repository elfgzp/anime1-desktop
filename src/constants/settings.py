"""
应用配置 - macOS 窗口和菜单设置
"""

# macOS 应用名称设置
MACOS_APP_NAME = "Anime1"
MACOS_BUNDLE_ID = "com.anime1.desktop"

# 窗口默认设置
DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800

# 视频播放设置（解决 webview 播放问题）
VIDEO_SETTINGS = {
    # 启用 HLS 流媒体支持
    "enable_hls": True,
    # 启用自动播放
    "autoplay": True,
    # 视频格式白名单
    "allowed_formats": ["video/mp4", "video/webm", "video/x-m4v", "application/vnd.apple.mpegurl"],
}

# 开发者工具设置
DEVTOOLS_ENABLED = False

# WebView 性能设置 - 已弃用，pywebview 5.x 在 Windows 上存在兼容性问题
# WEBVIEW_SETTINGS = {}

# 开发者工具快捷键
DEVTOOLS_SHORTCUT = "Cmd+Option+I"  # macOS: Option+Cmd+I
