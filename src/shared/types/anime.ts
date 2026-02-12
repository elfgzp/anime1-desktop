/**
 * 番剧相关类型定义
 * 
 * 对应原项目:
 * - src/models/anime.py
 * - src/models/favorite.py
 * - src/models/playback_history.py
 * - src/models/cover_cache.py
 */

// ==========================================
// 基础番剧类型
// ==========================================

/**
 * 番剧基础信息
 * 对应: src/models/anime.py - Anime dataclass
 */
export interface Anime {
  id: string
  title: string
  detailUrl: string
  episode: number
  coverUrl?: string
  year?: string
  season?: string
  subtitleGroup?: string
  matchScore?: number
  matchSource?: string
}

/**
 * 番剧分页
 * 对应: src/models/anime.py - AnimePage dataclass
 */
export interface AnimePage {
  animeList: Anime[]
  currentPage: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

// ==========================================
// 剧集类型
// ==========================================

/**
 * 剧集信息
 */
export interface Episode {
  id: string
  title: string
  episode: string
  url: string
  date: string
}

// ==========================================
// Bangumi 类型
// ==========================================

/**
 * Bangumi 搜索返回项
 */
export interface BangumiSearchResult {
  id: number
  title: string
  titleCn?: string
  coverUrl?: string
  type?: string
  score?: number
  rank?: number
  date?: string
}

/**
 * Bangumi 详细信息
 * 对应: src/parser/cover_finder.py - Bangumi 数据格式
 */
export interface BangumiInfo {
  title: string
  subjectUrl: string
  coverUrl?: string
  rating?: number
  rank?: number
  type?: string
  date?: string
  summary?: string
  genres: string[]
  staff: Array<{
    name: string
    role: string
  }>
  cast: Array<{
    name: string
    character: string
  }>
}

// ==========================================
// 数据库模型类型
// ==========================================

/**
 * 收藏番剧
 * 对应: src/models/favorite.py - FavoriteAnime Model
 */
export interface FavoriteAnime {
  /** 数据库自增ID */
  dbId?: number
  /** 番剧ID (anime1.me 的 cat_id) */
  animeId: string
  title: string
  detailUrl: string
  /** 当前集数 */
  episode: number
  coverUrl?: string
  year?: string
  season?: string
  subtitleGroup?: string
  /** 上次观看到的集数 */
  lastEpisode?: number
  /** 添加时间 (timestamp) */
  addedAt: number
  /** 更新时间 (timestamp) */
  updatedAt: number
}

/**
 * 封面缓存
 * 对应: src/models/cover_cache.py - CoverCache Model
 */
export interface CoverCache {
  animeId: string
  title: string
  year?: string
  season?: string
  coverUrl?: string
  episode: number
  /** 封面数据 JSON 字符串 */
  coverData: Record<string, unknown>
  /** Bangumi 详细数据 */
  bangumiInfo?: BangumiInfo
  /** 缓存时间 (timestamp) */
  cachedAt: number
  /** 更新时间 (timestamp) */
  updatedAt: number
}

/**
 * 播放历史
 * 对应: src/models/playback_history.py - PlaybackHistory Model
 */
export interface PlaybackHistory {
  /** 唯一ID: `${animeId}_${episodeId}` */
  id: string
  animeId: string
  animeTitle: string
  episodeId: string
  /** 集数序号 */
  episodeNum: number
  /** 播放位置 (秒) */
  positionSeconds: number
  /** 总时长 (秒) */
  totalSeconds: number
  /** 最后观看时间 (timestamp) */
  lastWatchedAt: number
  coverUrl?: string
}

/**
 * 播放历史展示项（带格式化字段）
 */
export interface PlaybackHistoryDisplay extends PlaybackHistory {
  /** 格式化后的播放位置 (MM:SS 或 HH:MM:SS) */
  positionFormatted: string
  /** 播放进度百分比 (0-100) */
  progressPercent: number
}

// ==========================================
// 下载类型
// ==========================================

/** 下载任务状态 */
export type DownloadStatus = 'pending' | 'downloading' | 'paused' | 'completed' | 'error'

/**
 * 下载任务
 * 对应: src/services/video_downloader.py
 */
export interface DownloadTask {
  id: string
  animeId: string
  episodeId: string
  title: string
  episodeTitle: string
  url: string
  status: DownloadStatus
  /** 下载进度 0-100 */
  progress: number
  /** 下载速度 (bytes/s) */
  speed: number
  totalSize: number
  downloadedSize: number
  errorMessage?: string
  createdAt: number
  updatedAt: number
}

/**
 * 下载任务创建参数
 */
export interface CreateDownloadTaskParams {
  url: string
  filename: string
  animeId?: string
  episodeId?: string
  title?: string
  episodeTitle?: string
}

// ==========================================
// 缓存类型
// ==========================================

/**
 * 番剧缓存状态
 * 对应: src/services/anime_cache_service.py
 */
export interface CacheStatus {
  animeCount: number
  coversCached: number
  lastRefresh: string | null
  isRefreshing: boolean
  initialLoadComplete: boolean
  progress: CacheProgress
}

/**
 * 缓存进度
 */
export interface CacheProgress {
  currentPage: number
  totalPages: number
  currentIndex: number
  totalAnime: number
  isFetching: boolean
}

// ==========================================
// 视频播放类型
// ==========================================

/**
 * 视频源
 */
export interface VideoSource {
  iframeUrl?: string
  scriptUrl?: string
  playerPage: string
}

/**
 * 播放器状态
 */
export interface PlayerState {
  isPlaying: boolean
  currentTime: number
  duration: number
  volume: number
  isFullscreen: boolean
  isLoading: boolean
}

// ==========================================
// 设置类型 (基础定义，详细在 settings.ts)
// ==========================================

/**
 * 自动下载配置
 */
export interface AutoDownloadConfig {
  enabled: boolean
  downloadPath: string
  filters: {
    years: string[]
    seasons: string[]
  }
}

/**
 * 应用设置 (基础)
 */
export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  downloadPath: string
  autoDownloadEnabled: boolean
  autoDownloadFilters: {
    years: string[]
    seasons: string[]
  }
  autoPlayNext: boolean
  rememberPlaybackPosition: boolean
  defaultVolume: number
  updateChannel: 'stable' | 'test'
  autoCheckUpdates: boolean
}
