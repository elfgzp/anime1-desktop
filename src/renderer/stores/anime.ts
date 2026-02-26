/**
 * 番剧 Store
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Anime, Episode, AnimeWithProgress } from '@shared/types'

// 播放进度信息
interface PlaybackProgressInfo {
  episodeNum: number
  positionSeconds: number
  positionFormatted: string
  progressPercent: number
  lastWatchedAt: number | null
}

// 扩展的 Anime 类型，包含 UI 状态和播放进度
interface AnimeWithUIState extends Anime {
  coverLoaded?: boolean
  coverError?: boolean
  playbackProgress?: PlaybackProgressInfo | null
}

export const useAnimeStore = defineStore('anime', () => {
  // State
  const animeList = ref<AnimeWithUIState[]>([])
  const currentAnime = ref<AnimeWithUIState | null>(null)
  const episodes = ref<Episode[]>([])
  const currentPage = ref(1)
  const totalPages = ref(1)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)
  let coverRefreshTimer: ReturnType<typeof setInterval> | null = null

  // Getters
  const getAnimeById = computed(() => (id: string) => {
    return animeList.value.find(a => a.id === id)
  })

  // Actions
  async function fetchAnimeList(page = 1, withProgress = false) {
    loading.value = true
    error.value = null
    
    // 清除之前的定时器
    if (coverRefreshTimer) {
      clearInterval(coverRefreshTimer)
      coverRefreshTimer = null
    }
    
    try {
      // 如果请求播放进度，使用新的 API
      const result = withProgress 
        ? await window.api.anime.getListWithProgress({ page })
        : await window.api.anime.getList({ page })
      
      if (result.success && result.data) {
        // 初始化 UI 状态
        animeList.value = result.data.animeList.map((anime: Anime | AnimeWithProgress) => {
          const animeWithState: AnimeWithUIState = {
            ...anime,
            coverLoaded: false,
            coverError: false
          }
          // 如果包含播放进度，也添加到状态中
          if ('playbackProgress' in anime) {
            animeWithState.playbackProgress = anime.playbackProgress
          }
          return animeWithState
        })
        currentPage.value = result.data.currentPage
        totalPages.value = result.data.totalPages
        
        // 启动封面刷新定时器，检查后台加载的封面
        startCoverRefreshTimer()
      } else {
        error.value = result.error?.message || 'Failed to fetch anime list'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }
  
  // 启动封面刷新定时器
  function startCoverRefreshTimer() {
    // 清除之前的定时器
    if (coverRefreshTimer) {
      clearInterval(coverRefreshTimer)
    }
    
    // 立即刷新一次
    refreshCovers()
    
    // 每 3 秒刷新一次，最多刷新 10 次（30秒）
    let refreshCount = 0
    coverRefreshTimer = setInterval(() => {
      refreshCount++
      refreshCovers()
      
      // 如果所有封面都已加载或超过最大刷新次数，停止定时器
      const allLoaded = animeList.value.every(a => a.coverUrl || a.coverError)
      if (allLoaded || refreshCount >= 10) {
        if (coverRefreshTimer) {
          clearInterval(coverRefreshTimer)
          coverRefreshTimer = null
        }
      }
    }, 3000)
  }
  
  // 刷新封面数据
  async function refreshCovers() {
    if (animeList.value.length === 0) return
    
    try {
      // 获取当前页的最新数据（只刷新封面）
      const result = await window.api.anime.getList({ page: currentPage.value })
      
      if (result.success && result.data) {
        // 更新封面 URL，保留 UI 状态和其他数据（如 playbackProgress）
        const freshData = result.data.animeList
        for (const freshAnime of freshData) {
          const existing = animeList.value.find(a => a.id === freshAnime.id)
          if (existing && freshAnime.coverUrl && !existing.coverUrl) {
            existing.coverUrl = freshAnime.coverUrl
            existing.year = freshAnime.year
            existing.season = freshAnime.season
            existing.subtitleGroup = freshAnime.subtitleGroup
            // 注意：保留 existing.playbackProgress，不要覆盖
          }
        }
      }
    } catch (e) {
      // 静默处理刷新错误
      console.debug('Failed to refresh covers:', e)
    }
  }

  async function fetchAnimeDetail(id: string) {
    loading.value = true
    error.value = null
    
    try {
      const result = await window.api.anime.getDetail({ id })
      
      if (result.success && result.data) {
        currentAnime.value = {
          ...result.data,
          coverLoaded: false,
          coverError: false
        }
      } else {
        error.value = result.error?.message || 'Failed to fetch anime detail'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchEpisodes(id: string) {
    loading.value = true
    error.value = null
    
    try {
      const result = await window.api.anime.getEpisodes({ id })
      
      if (result.success && result.data) {
        episodes.value = result.data.episodes || []
        if (result.data.anime) {
          currentAnime.value = {
            ...result.data.anime,
            coverLoaded: false,
            coverError: false
          }
        }
      } else {
        error.value = result.error?.message || 'Failed to fetch episodes'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function search(keyword: string, page = 1, withProgress = false) {
    loading.value = true
    error.value = null
    
    // 清除之前的定时器
    if (coverRefreshTimer) {
      clearInterval(coverRefreshTimer)
      coverRefreshTimer = null
    }
    
    try {
      // 如果请求播放进度，使用新的 API
      const result = withProgress
        ? await window.api.anime.searchWithProgress({ keyword, page })
        : await window.api.anime.search({ keyword, page })
      
      if (result.success && result.data) {
        // 初始化 UI 状态
        animeList.value = result.data.animeList.map((anime: Anime | AnimeWithProgress) => {
          const animeWithState: AnimeWithUIState = {
            ...anime,
            coverLoaded: false,
            coverError: false
          }
          // 如果包含播放进度，也添加到状态中
          if ('playbackProgress' in anime) {
            animeWithState.playbackProgress = anime.playbackProgress
          }
          return animeWithState
        })
        currentPage.value = result.data.currentPage
        totalPages.value = result.data.totalPages
        
        // 启动封面刷新定时器
        startCoverRefreshTimer()
      } else {
        error.value = result.error?.message || 'Search failed'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function refreshCache() {
    try {
      await window.api.anime.refreshCache()
    } catch (e) {
      error.value = String(e)
    }
  }

  // 清理函数
  function cleanup() {
    if (coverRefreshTimer) {
      clearInterval(coverRefreshTimer)
      coverRefreshTimer = null
    }
  }

  return {
    // State
    animeList,
    currentAnime,
    episodes,
    currentPage,
    totalPages,
    loading,
    error,
    initialized,
    // Getters
    getAnimeById,
    // Actions
    fetchAnimeList,
    fetchAnimeDetail,
    fetchEpisodes,
    search,
    refreshCache,
    refreshCovers,
    cleanup
  }
})
