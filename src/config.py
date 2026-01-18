"""Application constants and configuration."""
import os
from pathlib import Path

# Paths
# Use abspath to ensure we get the absolute path even when __file__ is relative
PROJECT_ROOT = Path(os.path.abspath(__file__)).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
STATIC_DIST = STATIC_DIR / "dist"
STATIC_CACHE_DIR = STATIC_DIR / "vendor"

# HTTP Configuration
DEFAULT_TIMEOUT = 30
DEFAULT_DELAY = 0.3
DEFAULT_PORT = 5172
DEFAULT_HOST = "127.0.0.1"

# HTTP Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 1
RETRY_STATUS_CODES = [500, 502, 503, 504]

# Anime1.me Configuration
ANIME1_BASE_URL = "https://anime1.me"
ANIME1_API_URL = "https://anime1.me/animelist.json"

# Bangumi Configuration
BANGUMI_BASE_URL = "https://bangumi.tv"
BANGUMI_SEARCH_URL = "https://bangumi.tv/subject_search/{keyword}?cat=2"

# Wikipedia Configuration
WIKIPEDIA_BASE_URL = "https://zh.wikipedia.org"
WIKIPEDIA_SEARCH_URL = "https://zh.wikipedia.org/w/index.php?search={keyword}&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1"

# Cover Finder Configuration
BANGUMI_RESULT_LIMIT = 5
MIN_MATCH_SCORE = 30
MIN_TITLE_LENGTH = 4
MIN_ENGLISH_LENGTH = 5
MIN_CHINESE_CHARS = 2

# Score Thresholds
SCORE_EXACT = 100
SCORE_CONTAINS = 90
SCORE_SUBSTRING = 85
SCORE_WORD_OVERLAP = 50
SCORE_CHINESE_OVERLAP = 40

# Stop Words for Keyword Extraction
STOP_WORDS = [
    "第二季", "第一季", "第三季", "第二", "第一", "第三",
    "可以幫忙", "嗎", "?", "！", "為了", "的", "是",
]

# Seasons
SEASONS = ["冬季", "春季", "夏季", "秋季"]

# Subtitle Group Keywords
SUBTITLE_KEYWORDS = ["字幕組", "字幕", "翻譯", "翻"]

# Regex Patterns
PATTERNS = {
    # Anime1 list pattern
    "anime1_list": r'<a href="(https://anime1\.me/(\d+))">([^<]+)\[(\d+)\]</a>',
    # Year pattern (2023-2029)
    "year": r"(?:202[3-9]|20[3-9]\d)",
    # Page number in URL
    "page_number": r"/category/(\d+)",
    # Clean title (Chinese/Japanese punctuation and numbers)
    "clean_title": r"[【】\(\)（）\[\]0-9\s\-第二季第三季第一季]",
    "clean_title2": r"[【】\(\)（）\[\]\s\-]",
    # English words extraction
    "english_words": r"[a-zA-Z]+",
    # Non-word characters
    "non_word_chars": r"[^\w\s]",
    # Bracket content removal
    "bracket_content": r"[【】\(\)（）\[\]].*?[】\)）\]]",
    "brackets": r"[【】\(\)（）\[\]]",
}

# CSS Selectors
SELECTORS = {
    "anime1_item": "li.item a.subjectCover",
    "page_link": 'a[href*="category/"]',
}

# Default values
DEFAULTS = {
    "page": 1,
    "episode": 0,
    "page_size": 20,  # Number of items per page
}

# Page size for pagination
PAGE_SIZE = 20

# Update Checker Configuration
GITHUB_REPO_OWNER = "elfgzp"
GITHUB_REPO_NAME = "anime1-desktop"
UPDATE_CHANNEL = "stable"  # "stable" or "test"

# Cache Configuration
CACHE_REFRESH_INTERVAL = 300  # 5 minutes between cache refreshes
ANIME_LIST_CACHE_TTL = 600  # 10 minutes TTL for anime list cache
