/**
 * 收藏 Store
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { FavoriteAnime } from '@shared/types'

export const useFavoriteStore = defineStore('favorite', () => {
  // State
  const favorites = ref<FavoriteAnime[]>([])
  const loading = ref(false)
  const hasUpdates = ref(false)

  // Getters
  const favoriteIds = computed(() => new Set(favorites.value.map(f => f.animeId)))
  
  const isFavorite = computed(() => (animeId: string) => {
    return favoriteIds.value.has(animeId)
  })

  // Actions
  async function loadFavorites() {
    loading.value = true
    
    try {
      const result = await window.api.favorite.getList()
      
      if (result.success && result.data) {
        favorites.value = result.data
      }
    } finally {
      loading.value = false
    }
  }

  async function addFavorite(anime: {
    animeId: string
    title: string
    coverUrl?: string
    detailUrl: string
    episode?: number
    year?: string
    season?: string
    subtitleGroup?: string
  }) {
    const result = await window.api.favorite.add(anime)
    
    if (result.success) {
      await loadFavorites()
    }
    
    return result.success
  }

  async function removeFavorite(animeId: string) {
    const result = await window.api.favorite.remove({ animeId })
    
    if (result.success) {
      await loadFavorites()
    }
    
    return result.success
  }

  async function toggleFavorite(anime: {
    animeId: string
    title: string
    coverUrl?: string
    detailUrl: string
    episode?: number
    year?: string
    season?: string
    subtitleGroup?: string
  }) {
    if (isFavorite.value(anime.animeId)) {
      return removeFavorite(anime.animeId)
    } else {
      return addFavorite(anime)
    }
  }

  // 批量检查收藏状态（用于首页）
  async function batchCheckStatus(animeIds: string[]): Promise<Record<string, boolean>> {
    if (animeIds.length === 0) return {}
    
    try {
      const result = await window.api.favorite.batchStatus({ ids: animeIds })
      if (result.success && result.data) {
        return result.data
      }
    } catch (error) {
      console.error('[FavoriteStore] Batch check status failed:', error)
    }
    return {}
  }

  return {
    favorites,
    loading,
    hasUpdates,
    isFavorite,
    loadFavorites,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    batchCheckStatus
  }
})
