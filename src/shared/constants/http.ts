/**
 * HTTP 相关常量
 * 
 * 对应原项目: src/constants/headers.py, src/config.py
 */

// ==========================================
// URL 配置
// ==========================================

export const URLS = {
  // Anime1
  ANIME1_BASE: 'https://anime1.me',
  ANIME1_API: 'https://anime1.me/animelist.json',
  
  // Bangumi
  BANGUMI_BASE: 'https://bangumi.tv',
  BANGUMI_API: 'https://api.bgm.tv',
  
  // Wikipedia
  WIKIPEDIA_BASE: 'https://zh.wikipedia.org'
} as const

// ==========================================
// HTTP 配置
// ==========================================

export const HTTP_CONFIG = {
  DEFAULT_TIMEOUT: 30000, // 30 seconds
  DEFAULT_DELAY: 300, // 300ms between requests
  MAX_RETRIES: 3,
  RETRY_BACKOFF: 1000, // 1 second
  RETRY_STATUS_CODES: [500, 502, 503, 504]
} as const

// ==========================================
// 请求头
// ==========================================

export const HEADERS = {
  USER_AGENT: 'User-Agent',
  ACCEPT: 'Accept',
  ACCEPT_LANGUAGE: 'Accept-Language',
  CONTENT_TYPE: 'Content-Type',
  REFERER: 'Referer',
  ORIGIN: 'Origin',
  RANGE: 'Range'
} as const

export const HEADER_VALUES = {
  USER_AGENT: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  ACCEPT_HTML: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  ACCEPT_JSON: 'application/json',
  ACCEPT_LANGUAGE: 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
  CONTENT_TYPE_FORM: 'application/x-www-form-urlencoded',
  CONTENT_TYPE_JSON: 'application/json'
} as const

// ==========================================
// 预定义请求头组合
// ==========================================

export const REQUEST_HEADERS = {
  DEFAULT: {
    [HEADERS.USER_AGENT]: HEADER_VALUES.USER_AGENT,
    [HEADERS.ACCEPT]: HEADER_VALUES.ACCEPT_HTML,
    [HEADERS.ACCEPT_LANGUAGE]: HEADER_VALUES.ACCEPT_LANGUAGE
  },
  
  API: {
    [HEADERS.USER_AGENT]: HEADER_VALUES.USER_AGENT,
    [HEADERS.ACCEPT]: HEADER_VALUES.ACCEPT_JSON,
    [HEADERS.CONTENT_TYPE]: HEADER_VALUES.CONTENT_TYPE_FORM
  },
  
  ANIME1: {
    [HEADERS.USER_AGENT]: HEADER_VALUES.USER_AGENT,
    [HEADERS.ACCEPT]: HEADER_VALUES.ACCEPT_HTML,
    [HEADERS.ACCEPT_LANGUAGE]: HEADER_VALUES.ACCEPT_LANGUAGE,
    [HEADERS.REFERER]: 'https://anime1.me/',
    [HEADERS.ORIGIN]: 'https://anime1.me'
  },
  
  JSON: {
    [HEADERS.USER_AGENT]: HEADER_VALUES.USER_AGENT,
    [HEADERS.ACCEPT]: HEADER_VALUES.ACCEPT_JSON,
    [HEADERS.ACCEPT_LANGUAGE]: HEADER_VALUES.ACCEPT_LANGUAGE
  }
} as const
