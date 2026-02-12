/**
 * API 请求和响应类型定义
 * 
 * 对应原项目: src/routes/ 下的所有 Flask API
 */

import type {
  Anime,
  AnimePage,
  Episode,
  BangumiInfo,
  CacheStatus,
  FavoriteAnime,
  PlaybackHistory,
  DownloadTask,
  CreateDownloadTaskParams,
  VideoSource
} from './anime'

// ==========================================
// 基础 API 类型
// ==========================================

/**
 * API 标准响应格式
 */
export interface APIResponse<T = unknown> {
  success: boolean
  data?: T
  error?: {
    code?: string
    message: string
  }
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number
  pageSize?: number
}

// ==========================================
// 番剧相关 API
// ==========================================

/**
 * 获取番剧列表
 * IPC: anime:list
 */
export interface GetAnimeListRequest extends PaginationParams {}

export type GetAnimeListResponse = APIResponse<AnimePage>

/**
 * 获取番剧详情
 * IPC: anime:detail
 */
export interface GetAnimeDetailRequest {
  id: string
}

export type GetAnimeDetailResponse = APIResponse<Anime>

/**
 * 获取剧集列表
 * IPC: anime:episodes
 */
export interface GetEpisodesRequest {
  id: string
}

export type GetEpisodesResponse = APIResponse<{
  anime: Anime
  episodes: Episode[]
  totalEpisodes: number
}>

/**
 * 搜索番剧
 * IPC: anime:search
 */
export interface SearchAnimeRequest extends PaginationParams {
  keyword: string
}

export type SearchAnimeResponse = APIResponse<AnimePage>

/**
 * 获取 Bangumi 信息
 * IPC: anime:bangumi
 */
export interface GetBangumiInfoRequest {
  id: string
}

export type GetBangumiInfoResponse = APIResponse<BangumiInfo>

/**
 * 获取缓存状态
 * IPC: anime:cache:status
 */
export type GetCacheStatusResponse = APIResponse<CacheStatus>

/**
 * 刷新缓存
 * IPC: anime:cache:refresh
 */
export type RefreshCacheResponse = APIResponse<void>

// ==========================================
// 收藏相关 API
// ==========================================

/**
 * 获取收藏列表
 * IPC: favorite:list
 */
export type GetFavoritesResponse = APIResponse<FavoriteAnime[]>

/**
 * 添加收藏
 * IPC: favorite:add
 */
export interface AddFavoriteRequest {
  animeId: string
  title: string
  coverUrl?: string
  detailUrl: string
  episode?: number
  year?: string
  season?: string
  subtitleGroup?: string
}

export type AddFavoriteResponse = APIResponse<void>

/**
 * 移除收藏
 * IPC: favorite:remove
 */
export interface RemoveFavoriteRequest {
  animeId: string
}

export type RemoveFavoriteResponse = APIResponse<void>

/**
 * 检查是否已收藏
 * IPC: favorite:check
 */
export interface CheckFavoriteRequest {
  animeId: string
}

export type CheckFavoriteResponse = APIResponse<boolean>

// ==========================================
// 播放历史相关 API
// ==========================================

/**
 * 获取播放历史
 * IPC: history:list
 */
export type GetPlaybackHistoryResponse = APIResponse<PlaybackHistory[]>

/**
 * 添加播放记录
 * IPC: history:add
 */
export interface AddPlaybackHistoryRequest {
  animeId: string
  animeTitle: string
  episodeId: string
  episodeNum: number
  positionSeconds: number
  totalSeconds: number
  coverUrl?: string
}

export type AddPlaybackHistoryResponse = APIResponse<void>

/**
 * 清除播放历史
 * IPC: history:clear
 */
export type ClearPlaybackHistoryResponse = APIResponse<void>

// ==========================================
// 下载相关 API
// ==========================================

/**
 * 获取下载任务列表
 * IPC: download:list
 */
export type GetDownloadListResponse = APIResponse<DownloadTask[]>

/**
 * 添加下载任务
 * IPC: download:add
 */
export interface AddDownloadRequest extends CreateDownloadTaskParams {}

export type AddDownloadResponse = APIResponse<DownloadTask>

/**
 * 暂停下载
 * IPC: download:pause
 */
export interface PauseDownloadRequest {
  taskId: string
}

export type PauseDownloadResponse = APIResponse<void>

/**
 * 恢复下载
 * IPC: download:resume
 */
export interface ResumeDownloadRequest {
  taskId: string
}

export type ResumeDownloadResponse = APIResponse<void>

/**
 * 取消下载
 * IPC: download:cancel
 */
export interface CancelDownloadRequest {
  taskId: string
}

export type CancelDownloadResponse = APIResponse<void>

/**
 * 删除下载任务
 * IPC: download:remove
 */
export interface RemoveDownloadRequest {
  taskId: string
}

export type RemoveDownloadResponse = APIResponse<void>

// ==========================================
// 设置相关 API
// ==========================================

/**
 * 获取设置
 * IPC: settings:get
 */
export interface GetSettingRequest {
  key: string
}

export type GetSettingResponse = APIResponse<string | null>

/**
 * 保存设置
 * IPC: settings:set
 */
export interface SetSettingRequest {
  key: string
  value: string
}

export type SetSettingResponse = APIResponse<void>

/**
 * 获取所有设置
 * IPC: settings:getAll
 */
export type GetAllSettingsResponse = APIResponse<Record<string, string>>

// ==========================================
// 系统相关 API
// ==========================================

/**
 * 窗口状态
 * IPC: window:getState
 */
export interface WindowState {
  maximized: boolean
  minimized: boolean
  fullscreen: boolean
  focused: boolean
}

export type GetWindowStateResponse = APIResponse<WindowState>

/**
 * 在资源管理器中显示
 * IPC: system:showItemInFolder
 */
export interface ShowItemInFolderRequest {
  path: string
}

/**
 * 用外部浏览器打开链接
 * IPC: system:openExternal
 */
export interface OpenExternalRequest {
  url: string
}

// ==========================================
// 更新相关 API
// ==========================================

/**
 * 更新信息
 */
export interface UpdateInfo {
  version: string
  releaseNotes: string
  releaseDate: string
}

/**
 * 检查更新
 * IPC: update:check
 */
export type CheckUpdateResponse = APIResponse<UpdateInfo | null>

/**
 * 下载更新
 * IPC: update:download
 */
export type DownloadUpdateResponse = APIResponse<void>

/**
 * 安装更新
 * IPC: update:install
 */
export type InstallUpdateResponse = APIResponse<void>
