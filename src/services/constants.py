"""Constants for update checker service."""

# Version parsing constants
VERSION_PREFIXES = "vV"
VERSION_SEPARATOR = "-"
VERSION_COMPONENT_COUNT = 3
DEFAULT_VERSION_COMPONENT = 0

# Pre-release types
PRE_RELEASE_ALPHA = "alpha"
PRE_RELEASE_BETA = "beta"
PRE_RELEASE_RC = "rc"

# Pre-release type order (for comparison)
PRE_RELEASE_ORDER = {
    PRE_RELEASE_ALPHA: 1,
    PRE_RELEASE_BETA: 2,
    PRE_RELEASE_RC: 3,
}

# Pre-release regex pattern
PRE_RELEASE_PATTERN = r'^(rc|beta|alpha)\.?(\d+)?'

# GitHub API constants
GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_ACCEPT_HEADER = "application/vnd.github.v3+json"
GITHUB_USER_AGENT = "Anime1-Desktop-Updater/1.0"

# GitHub API endpoints
GITHUB_RELEASES_ENDPOINT = "/releases"
GITHUB_LATEST_RELEASE_ENDPOINT = "/releases/latest"

# GitHub API response fields
API_FIELD_TAG_NAME = "tag_name"
API_FIELD_ASSETS = "assets"
API_FIELD_PRERELEASE = "prerelease"
API_FIELD_BROWSER_DOWNLOAD_URL = "browser_download_url"
API_FIELD_NAME = "name"
API_FIELD_SIZE = "size"
API_FIELD_PUBLISHED_AT = "published_at"
API_FIELD_BODY = "body"

# HTTP status codes
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404

# Rate limit header
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_EXHAUSTED = "0"

# Update channel values
CHANNEL_STABLE = "stable"
CHANNEL_TEST = "test"

# Platform detection keywords
PLATFORM_WINDOWS_KEYWORDS = ["windows", "win"]
PLATFORM_MACOS_KEYWORDS = ["macos", "mac", "darwin"]
PLATFORM_LINUX_KEYWORDS = ["linux"]

# Architecture detection keywords
ARCH_X64_KEYWORDS = ["x64", "amd64", "x86_64"]
ARCH_ARM64_KEYWORDS = ["arm64", "aarch64", "m1", "m2", "m3", "apple"]
ARCH_X86_KEYWORDS = ["x86", "i386", "i686"]

# Platform names
PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS = "macos"
PLATFORM_LINUX = "linux"

# Architecture names
ARCH_X64 = "x64"
ARCH_ARM64 = "arm64"
ARCH_X86 = "x86"

# System platform mappings
SYSTEM_DARWIN = "darwin"
SYSTEM_WINDOWS = "windows"
SYSTEM_LINUX = "linux"

# Machine architecture mappings
MACHINE_X86_64 = "x86_64"
MACHINE_AMD64 = "amd64"
MACHINE_ARM64 = "arm64"
MACHINE_AARCH64 = "aarch64"
MACHINE_I386 = "i386"
MACHINE_I686 = "i686"
MACHINE_X86 = "x86"

# Architecture exclusion keywords (for fallback matching)
ARCH_EXCLUDE_ARM = "arm"
ARCH_EXCLUDE_AARCH = "aarch"
