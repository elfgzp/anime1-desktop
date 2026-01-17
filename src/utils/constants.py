"""Constants for version utilities."""

# Environment variable
ENV_VERSION = "ANIME1_VERSION"

# Version fallback values
VERSION_DEV = "dev"
VERSION_DEV_PREFIX = "dev-"

# Git command constants
GIT_COMMAND = "git"
GIT_DESCRIBE_CMD = "describe"
GIT_DESCRIBE_TAGS_FLAG = "--tags"
GIT_DESCRIBE_ABBREV_FLAG = "--abbrev=0"
GIT_REV_PARSE_CMD = "rev-parse"
GIT_REV_PARSE_SHORT_FLAG = "--short"
GIT_HEAD_REF = "HEAD"

# Git command timeout (seconds)
GIT_COMMAND_TIMEOUT = 5

# Git command success return code
GIT_SUCCESS_CODE = 0

# Version prefix to strip
VERSION_PREFIXES = "vV"

# Window title constants
WINDOW_TITLE_BASE = "Anime1 桌面版"
WINDOW_TITLE_VERSION_PREFIX = "v"
WINDOW_TITLE_TEST_SUFFIX = "测试版"

# Commit ID display length
COMMIT_ID_DISPLAY_LENGTH = 8
