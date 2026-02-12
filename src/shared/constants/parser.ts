/**
 * 解析相关常量
 * 
 * 对应原项目: src/config.py 中的 Patterns, Seasons 等
 */

// ==========================================
// 季节
// ==========================================

export const SEASONS = ['冬季', '春季', '夏季', '秋季'] as const

// ==========================================
// 字幕组关键词
// ==========================================

export const SUBTITLE_KEYWORDS = ['字幕組', '字幕', '翻譯', '翻'] as const

// ==========================================
// 停用词
// ==========================================

export const STOP_WORDS = [
  '第二季', '第一季', '第三季', '第二', '第一', '第三',
  '可以幫忙', '嗎', '?', '！', '為了', '的', '是'
] as const

// ==========================================
// 正则表达式
// ==========================================

export const PATTERNS = {
  // Anime1 列表模式
  ANIME1_LIST: /<a href="(https:\/\/anime1\.me\/(\d+))">([^<]+)\[(\d+)\]<\/a>/,
  
  // 年份 (2023-2029)
  YEAR: /(?:202[3-9]|20[3-9]\d)/,
  
  // 页码
  PAGE_NUMBER: /\/category\/(\d+)/,
  
  // 清理标题
  CLEAN_TITLE: /[【】\(\)（）\[\]0-9\s\-第二季第三季第一季]/g,
  CLEAN_TITLE2: /[【】\(\)（）\[\]\s\-]/g,
  
  // 英文单词
  ENGLISH_WORDS: /[a-zA-Z]+/g,
  
  // 非单词字符
  NON_WORD_CHARS: /[^\w\s]/g,
  
  // 括号内容
  BRACKET_CONTENT: /[【】\(\)（）\[\]].*?[】\)）\]]/g,
  BRACKETS: /[【】\(\)（）\[\]]/g
} as const

// ==========================================
// Bangumi 匹配配置
// ==========================================

export const BANGUMI_CONFIG = {
  RESULT_LIMIT: 5,
  MIN_MATCH_SCORE: 30,
  MIN_TITLE_LENGTH: 4,
  MIN_ENGLISH_LENGTH: 5,
  MIN_CHINESE_CHARS: 2
} as const

// ==========================================
// 匹配分数
// ==========================================

export const MATCH_SCORES = {
  EXACT: 100,
  CONTAINS: 90,
  SUBSTRING: 85,
  WORD_OVERLAP: 50,
  CHINESE_OVERLAP: 40
} as const

// ==========================================
// CSS 选择器
// ==========================================

export const SELECTORS = {
  ANIME1_ITEM: 'li.item a.subjectCover',
  PAGE_LINK: 'a[href*="category/"]'
} as const
