/**
 * 番剧相关类型定义
 * 
 * 对应原项目: src/models/anime.py
 */

// 番剧基础信息
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

// 剧集信息
export interface Episode {
  id: string
  title: string
  episode: string
  url: string
  date: string
}

// 番剧分页
export interface AnimePage {
  animeList: Anime[]
  currentPage: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

// Bangumi 信息
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

// 缓存状态
export interface CacheStatus {
  animeCount: number
  coversCached: number
  lastRefresh: string | null
  isRefreshing: boolean
  initialLoadComplete: boolean
  progress: {
    currentPage: number
    totalPages: number
    currentIndex: number
    totalAnime: number
    isFetching: boolean
  }
}

// 视频源
export interface VideoSource {
  iframeUrl?: string
  scriptUrl?: string
  playerPage: string
}

// 收藏
export interface FavoriteAnime {
  id: number
  animeId: string
  title: string
  coverUrl?: string
  detailUrl: string
  createdAt: number
}

// 播放历史
export interface PlaybackHistory {
  id: number
  animeId: string
  episodeId: string
  title: string
  episodeTitle: string
  progress: number
  duration: number
  playedAt: number
}

// 下载任务
export interface DownloadTask {
  id: string
  animeId: string
  episodeId: string
  title: string
  episodeTitle: string
  url: string
  status: 'pending' | 'downloading' | 'paused' | 'completed' | 'error'
  progress: number
  speed: number
  totalSize: number
  downloadedSize: number
  errorMessage?: string
  createdAt: number
  updatedAt: number
}

// 自动下载配置
export interface AutoDownloadConfig {
  enabled: boolean
  downloadPath: string
  filters: {
    years: string[]
    seasons: string[]
  }
}

// 应用设置
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

// API 响应
export interface APIResponse<T = unknown> {
  success: boolean
  data?: T
  error?: {
    code?: string
    message: string
  }
}
