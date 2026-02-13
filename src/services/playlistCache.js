/**
 * Playlist Cache Service
 * Caches anime list and detail pages with TTL support
 */

import Store from 'electron-store';

// Default TTL values (in milliseconds)
const DEFAULT_TTL = {
  animeList: 5 * 60 * 1000,      // 5 minutes for anime list
  animeDetail: 30 * 60 * 1000,   // 30 minutes for anime details
  episodes: 10 * 60 * 1000,      // 10 minutes for episodes
};

// Create a separate store for playlist cache
let playlistStore = null;

function getStore() {
  if (!playlistStore) {
    playlistStore = new Store({
      name: 'playlist-cache',
      projectName: 'anime1-desktop-electron-forge',
      clearInvalidConfig: true,
      defaults: {
        animeList: null,      // { data: [...], timestamp: number }
        animeDetails: {},     // { [animeId]: { data: {...}, timestamp: number } }
        episodes: {},         // { [animeId]: { data: [...], timestamp: number } }
        version: 1
      }
    });
  }
  return playlistStore;
}

/**
 * Check if cache entry is valid
 */
function isValidCache(entry, ttl) {
  if (!entry || !entry.timestamp || !entry.data) {
    return false;
  }
  return Date.now() - entry.timestamp < ttl;
}

/**
 * Get cached anime list
 */
export function getCachedAnimeList() {
  try {
    const store = getStore();
    const entry = store.get('animeList');
    
    if (isValidCache(entry, DEFAULT_TTL.animeList)) {
      console.log('[PlaylistCache] Anime list cache hit');
      return entry.data;
    }
    
    return null;
  } catch (error) {
    console.error('[PlaylistCache] Error getting anime list cache:', error.message);
    return null;
  }
}

/**
 * Set cached anime list
 */
export function setCachedAnimeList(data) {
  try {
    const store = getStore();
    store.set('animeList', {
      data,
      timestamp: Date.now()
    });
    console.log(`[PlaylistCache] Cached anime list with ${data.length} items`);
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error setting anime list cache:', error.message);
    return false;
  }
}

/**
 * Get cached anime detail
 */
export function getCachedAnimeDetail(animeId) {
  try {
    const store = getStore();
    const entry = store.get(`animeDetails.${animeId}`);
    
    if (isValidCache(entry, DEFAULT_TTL.animeDetail)) {
      console.log(`[PlaylistCache] Anime detail cache hit for ${animeId}`);
      return entry.data;
    }
    
    return null;
  } catch (error) {
    console.error('[PlaylistCache] Error getting anime detail cache:', error.message);
    return null;
  }
}

/**
 * Set cached anime detail
 */
export function setCachedAnimeDetail(animeId, data) {
  try {
    const store = getStore();
    store.set(`animeDetails.${animeId}`, {
      data,
      timestamp: Date.now()
    });
    console.log(`[PlaylistCache] Cached anime detail for ${animeId}`);
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error setting anime detail cache:', error.message);
    return false;
  }
}

/**
 * Get cached episodes
 */
export function getCachedEpisodes(animeId) {
  try {
    const store = getStore();
    const entry = store.get(`episodes.${animeId}`);
    
    if (isValidCache(entry, DEFAULT_TTL.episodes)) {
      console.log(`[PlaylistCache] Episodes cache hit for ${animeId}`);
      return entry.data;
    }
    
    return null;
  } catch (error) {
    console.error('[PlaylistCache] Error getting episodes cache:', error.message);
    return null;
  }
}

/**
 * Set cached episodes
 */
export function setCachedEpisodes(animeId, data) {
  try {
    const store = getStore();
    store.set(`episodes.${animeId}`, {
      data,
      timestamp: Date.now()
    });
    console.log(`[PlaylistCache] Cached ${data.length} episodes for ${animeId}`);
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error setting episodes cache:', error.message);
    return false;
  }
}

/**
 * Invalidate anime list cache
 */
export function invalidateAnimeList() {
  try {
    const store = getStore();
    store.set('animeList', null);
    console.log('[PlaylistCache] Invalidated anime list cache');
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error invalidating anime list cache:', error.message);
    return false;
  }
}

/**
 * Invalidate anime detail cache
 */
export function invalidateAnimeDetail(animeId) {
  try {
    const store = getStore();
    const details = store.get('animeDetails') || {};
    delete details[animeId];
    store.set('animeDetails', details);
    console.log(`[PlaylistCache] Invalidated anime detail cache for ${animeId}`);
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error invalidating anime detail cache:', error.message);
    return false;
  }
}

/**
 * Invalidate episodes cache
 */
export function invalidateEpisodes(animeId) {
  try {
    const store = getStore();
    const episodes = store.get('episodes') || {};
    delete episodes[animeId];
    store.set('episodes', episodes);
    console.log(`[PlaylistCache] Invalidated episodes cache for ${animeId}`);
    return true;
  } catch (error) {
    console.error('[PlaylistCache] Error invalidating episodes cache:', error.message);
    return false;
  }
}

/**
 * Get cache statistics
 */
export function getCacheStats() {
  try {
    const store = getStore();
    const animeList = store.get('animeList');
    const animeDetails = store.get('animeDetails') || {};
    const episodes = store.get('episodes') || {};
    
    const stats = {
      animeList: {
        cached: !!animeList,
        valid: isValidCache(animeList, DEFAULT_TTL.animeList),
        itemCount: animeList?.data?.length || 0,
        timestamp: animeList?.timestamp || null,
        age: animeList?.timestamp ? Date.now() - animeList.timestamp : null,
      },
      animeDetails: {
        count: Object.keys(animeDetails).length,
        validCount: Object.entries(animeDetails).filter(([_, entry]) => 
          isValidCache(entry, DEFAULT_TTL.animeDetail)
        ).length,
      },
      episodes: {
        count: Object.keys(episodes).length,
        validCount: Object.entries(episodes).filter(([_, entry]) => 
          isValidCache(entry, DEFAULT_TTL.episodes)
        ).length,
      },
      ttl: DEFAULT_TTL,
    };
    
    return stats;
  } catch (error) {
    console.error('[PlaylistCache] Error getting cache stats:', error.message);
    return null;
  }
}

/**
 * Clear all playlist cache
 */
export function clearAllCache() {
  try {
    const store = getStore();
    const animeDetails = store.get('animeDetails') || {};
    const episodes = store.get('episodes') || {};
    
    const stats = {
      animeList: store.get('animeList') ? 1 : 0,
      animeDetails: Object.keys(animeDetails).length,
      episodes: Object.keys(episodes).length,
    };
    
    store.set({
      animeList: null,
      animeDetails: {},
      episodes: {},
    });
    
    console.log('[PlaylistCache] Cleared all cache:', stats);
    return stats;
  } catch (error) {
    console.error('[PlaylistCache] Error clearing cache:', error.message);
    return null;
  }
}

/**
 * Clear expired cache entries
 */
export function clearExpiredCache() {
  try {
    const store = getStore();
    const animeDetails = store.get('animeDetails') || {};
    const episodes = store.get('episodes') || {};
    
    let clearedDetails = 0;
    let clearedEpisodes = 0;
    
    // Clear expired anime details
    for (const [id, entry] of Object.entries(animeDetails)) {
      if (!isValidCache(entry, DEFAULT_TTL.animeDetail)) {
        delete animeDetails[id];
        clearedDetails++;
      }
    }
    
    // Clear expired episodes
    for (const [id, entry] of Object.entries(episodes)) {
      if (!isValidCache(entry, DEFAULT_TTL.episodes)) {
        delete episodes[id];
        clearedEpisodes++;
      }
    }
    
    store.set('animeDetails', animeDetails);
    store.set('episodes', episodes);
    
    console.log(`[PlaylistCache] Cleared ${clearedDetails} expired details, ${clearedEpisodes} expired episodes`);
    return { clearedDetails, clearedEpisodes };
  } catch (error) {
    console.error('[PlaylistCache] Error clearing expired cache:', error.message);
    return null;
  }
}

/**
 * Initialize playlist cache
 */
export function initPlaylistCache() {
  getStore();
  console.log('[PlaylistCache] Initialized');
  
  // Clear expired entries on startup
  clearExpiredCache();
  
  // Schedule periodic cleanup every hour
  setInterval(clearExpiredCache, 60 * 60 * 1000);
}

export default {
  initPlaylistCache,
  getCachedAnimeList,
  setCachedAnimeList,
  getCachedAnimeDetail,
  setCachedAnimeDetail,
  getCachedEpisodes,
  setCachedEpisodes,
  invalidateAnimeList,
  invalidateAnimeDetail,
  invalidateEpisodes,
  getCacheStats,
  clearAllCache,
  clearExpiredCache,
};
