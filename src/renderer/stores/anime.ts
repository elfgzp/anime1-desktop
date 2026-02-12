/**
 * 番剧 Store
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Anime, AnimePage, Episode } from '@shared/types'

export const useAnimeStore = defineStore('anime', () => {
  // State
  const animeList = ref<Anime[]>([])
  const currentAnime = ref<Anime | null>(null)
  const episodes = ref<Episode[]>([])
  const currentPage = ref(1)
  const totalPages = ref(1)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)

  // Getters
  const getAnimeById = computed(() => (id: string) => {
    return animeList.value.find(a => a.id === id)
  })

  // Actions
  async function fetchAnimeList(page = 1) {
    loading.value = true
    error.value = null
    
    try {
      const result = await window.api.anime.getList({ page })
      
      if (result.success && result.data) {
        animeList.value = result.data.animeList
        currentPage.value = result.data.currentPage
        totalPages.value = result.data.totalPages
      } else {
        error.value = result.error?.message || 'Failed to fetch anime list'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchAnimeDetail(id: string) {
    loading.value = true
    error.value = null
    
    try {
      const result = await window.api.anime.getDetail({ id })
      
      if (result.success && result.data) {
        currentAnime.value = result.data
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
        episodes.value = result.data.episodes
        currentAnime.value = result.data.anime
      } else {
        error.value = result.error?.message || 'Failed to fetch episodes'
      }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function search(keyword: string, page = 1) {
    loading.value = true
    error.value = null
    
    try {
      const result = await window.api.anime.search({ keyword, page })
      
      if (result.success && result.data) {
        animeList.value = result.data.animeList
        currentPage.value = result.data.currentPage
        totalPages.value = result.data.totalPages
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
    refreshCache
  }
})
