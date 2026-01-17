"""HTTP header constants."""

from typing import Final

# ============================================================================
# Common Request Headers
# ============================================================================

HEADER_USER_AGENT: Final[str] = "User-Agent"
HEADER_ACCEPT: Final[str] = "Accept"
HEADER_ACCEPT_LANGUAGE: Final[str] = "Accept-Language"
HEADER_CONTENT_TYPE: Final[str] = "Content-Type"
HEADER_REFERER: Final[str] = "Referer"
HEADER_ORIGIN: Final[str] = "Origin"
HEADER_RANGE: Final[str] = "Range"
HEADER_COOKIE: Final[str] = "Cookie"
HEADER_SET_COOKIE: Final[str] = "Set-Cookie"
HEADER_CONTENT_LENGTH: Final[str] = "Content-Length"
HEADER_CONTENT_RANGE: Final[str] = "Content-Range"
HEADER_CONTENT_TYPE: Final[str] = "Content-Type"
HEADER_ACCEPT_RANGES: Final[str] = "Accept-Ranges"

# ============================================================================
# CORS Headers
# ============================================================================

HEADER_ACCESS_CONTROL_ALLOW_ORIGIN: Final[str] = "Access-Control-Allow-Origin"
HEADER_ACCESS_CONTROL_ALLOW_METHODS: Final[str] = "Access-Control-Allow-Methods"
HEADER_ACCESS_CONTROL_ALLOW_HEADERS: Final[str] = "Access-Control-Allow-Headers"
HEADER_ACCESS_CONTROL_EXPOSE_HEADERS: Final[str] = "Access-Control-Expose-Headers"

# ============================================================================
# Security Headers
# ============================================================================

HEADER_X_FRAME_OPTIONS: Final[str] = "X-Frame-Options"
HEADER_X_CONTENT_TYPE_OPTIONS: Final[str] = "X-Content-Type-Options"
HEADER_CSP: Final[str] = "Content-Security-Policy"
HEADER_UPGRADE_INSECURE_REQUESTS: Final[str] = "Upgrade-Insecure-Requests"
HEADER_SET_COOKIE: Final[str] = "Set-Cookie"
HEADER_ACCESS_CONTROL_ALLOW_ORIGIN: Final[str] = "Access-Control-Allow-Origin"
HEADER_ACCESS_CONTROL_ALLOW_METHODS: Final[str] = "Access-Control-Allow-Methods"
HEADER_ACCESS_CONTROL_ALLOW_HEADERS: Final[str] = "Access-Control-Allow-Headers"

# ============================================================================
# Common Header Values
# ============================================================================

VALUE_ACCEPT_JSON: Final[str] = "application/json"
VALUE_ACCEPT_HTML: Final[str] = "text/html,*/*"
VALUE_ACCEPT_ALL: Final[str] = "*/*"
VALUE_CONTENT_TYPE_JSON: Final[str] = "application/json"
VALUE_CONTENT_TYPE_FORM: Final[str] = "application/x-www-form-urlencoded"
VALUE_CONTENT_TYPE_HTML: Final[str] = "text/html"
VALUE_USER_AGENT_DEFAULT: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
VALUE_ACCEPT_LANGUAGE_ZH_TW: Final[str] = "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
VALUE_ACCEPT_LANGUAGE_DEFAULT: Final[str] = VALUE_ACCEPT_LANGUAGE_ZH_TW
VALUE_ACCEPT_HTML: Final[str] = "text/html,*/*"
VALUE_ACCEPT_ALL: Final[str] = "*/*"
VALUE_UPGRADE_INSECURE_REQUESTS: Final[str] = "1"
VALUE_ACCEPT_APPLICATION_JSON: Final[str] = "application/json"
VALUE_RANGE_BYTES: Final[str] = "bytes"

# ============================================================================
# CORS Values
# ============================================================================

VALUE_CORS_ALLOW_ORIGIN_ALL: Final[str] = "*"
VALUE_CORS_ALLOW_METHODS_GET: Final[str] = "GET"
VALUE_CORS_ALLOW_METHODS_GET_OPTIONS: Final[str] = "GET, OPTIONS"
VALUE_CORS_ALLOW_METHODS_ALL: Final[str] = "GET, POST, OPTIONS"
VALUE_CORS_ALLOW_HEADERS_RANGE: Final[str] = "Range"

# ============================================================================
# Security Values
# ============================================================================

VALUE_X_FRAME_OPTIONS_ALLOWALL: Final[str] = "ALLOWALL"
VALUE_X_FRAME_OPTIONS_SAMEORIGIN: Final[str] = "SAMEORIGIN"
VALUE_X_CONTENT_TYPE_OPTIONS_NOSNIFF: Final[str] = "nosniff"

# ============================================================================
# Video/Media Headers
# ============================================================================

VALUE_CONTENT_TYPE_VIDEO_MP4: Final[str] = "video/mp4"
VALUE_CONTENT_TYPE_VIDEO_WEBM: Final[str] = "video/webm"
VALUE_CONTENT_TYPE_HLS: Final[str] = "application/x-mpegURL"
VALUE_CONTENT_TYPE_OCTET_STREAM: Final[str] = "application/octet-stream"

# ============================================================================
# Cookie Attributes
# ============================================================================

VALUE_COOKIE_PATH_ROOT: Final[str] = "/"

# ============================================================================
# Cache Control Headers (for static resources)
# ============================================================================

HEADER_CACHE_CONTROL: Final[str] = "Cache-Control"
HEADER_ETAG: Final[str] = "ETag"
HEADER_LAST_MODIFIED: Final[str] = "Last-Modified"
VALUE_CACHE_CONTROL_MAX_AGE: Final[str] = "public, max-age=31536000"
VALUE_CACHE_CONTROL_NO_CACHE: Final[str] = "no-cache, no-store, must-revalidate"

# ============================================================================
# Request Header Dictionaries (for common use cases)
# ============================================================================

# Default request headers for anime1.me API calls
REQUEST_HEADERS_API: Final[dict] = {
    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
    HEADER_ACCEPT: VALUE_ACCEPT_JSON,
    HEADER_CONTENT_TYPE: VALUE_CONTENT_TYPE_FORM,
}

# Default request headers for HTML pages
REQUEST_HEADERS_PAGE: Final[dict] = {
    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
    HEADER_ACCEPT: VALUE_ACCEPT_HTML,
    HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
}

# Default request headers with Referer for anime1.me
REQUEST_HEADERS_ANIME1_REF: Final[dict] = {
    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
    HEADER_ACCEPT: VALUE_ACCEPT_HTML,
    HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
    HEADER_REFERER: "https://anime1.me/",
    HEADER_ORIGIN: "https://anime1.me",
}

# Video streaming request headers
REQUEST_HEADERS_VIDEO: Final[dict] = {
    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
    HEADER_ACCEPT: VALUE_ACCEPT_ALL,
    HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
}

# JSON request headers
REQUEST_HEADERS_JSON: Final[dict] = {
    HEADER_USER_AGENT: VALUE_USER_AGENT_DEFAULT,
    HEADER_ACCEPT: VALUE_ACCEPT_JSON,
    HEADER_ACCEPT_LANGUAGE: VALUE_ACCEPT_LANGUAGE_ZH_TW,
}

# CORS response headers (for adding to responses)
CORS_HEADERS: Final[dict] = {
    HEADER_ACCESS_CONTROL_ALLOW_ORIGIN: VALUE_CORS_ALLOW_ORIGIN_ALL,
    HEADER_ACCESS_CONTROL_ALLOW_METHODS: VALUE_CORS_ALLOW_METHODS_GET_OPTIONS,
    HEADER_ACCESS_CONTROL_ALLOW_HEADERS: VALUE_CORS_ALLOW_HEADERS_RANGE,
}

# ============================================================================
# Common MIME Types
# ============================================================================

MIME_TYPE_JSON: Final[str] = "application/json"
MIME_TYPE_HTML: Final[str] = "text/html"
MIME_TYPE_CSS: Final[str] = "text/css"
MIME_TYPE_JAVASCRIPT: Final[str] = "application/javascript"
MIME_TYPE_PLAIN: Final[str] = "text/plain"
MIME_TYPE_XML: Final[str] = "application/xml"
