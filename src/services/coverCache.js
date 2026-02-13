/**
 * Cover Cache Service using electron-store (no native modules)
 */

import Store from 'electron-store';

const CACHE_TTL = 30 * 24 * 60 * 60 * 1000; // 30 days

// Create a separate store for cover cache
let coverStore = null;

function getStore() {
  if (!coverStore) {
    coverStore = new Store({
      name: 'cover-cache',
      projectName: 'anime1-desktop-electron-forge',
      clearInvalidConfig: true,
      defaults: {
        covers: {},
        version: 1
      }
    });
  }
  return coverStore;
}

/**
 * Get cached cover for an anime
 */
export function getCachedCover(animeId) {
  try {
    const store = getStore();
    const data = store.get(`covers.${animeId}`);
    
    if (data && data.cover_url) {
      // Check if cache is still valid
      if (Date.now() - data.cached_at < CACHE_TTL) {
        return data;
      }
    }
    return null;
  } catch (error) {
    console.error('[CoverCache] Error getting cover:', error.message);
    return null;
  }
}

/**
 * Get cached Bangumi info for an anime
 */
export function getCachedBangumiInfo(animeId) {
  try {
    const store = getStore();
    const data = store.get(`covers.${animeId}`);
    
    if (data && data.bangumi_info) {
      // Check if cache is still valid
      if (Date.now() - data.cached_at < CACHE_TTL) {
        return data.bangumi_info;
      }
    }
    return null;
  } catch (error) {
    console.error('[CoverCache] Error getting Bangumi info:', error.message);
    return null;
  }
}

/**
 * Set cached Bangumi info for an anime
 */
export function setCachedBangumiInfo(animeId, bangumiInfo) {
  try {
    const store = getStore();
    const existing = store.get(`covers.${animeId}`) || {};
    
    store.set(`covers.${animeId}`, {
      ...existing,
      bangumi_info: bangumiInfo,
      cached_at: Date.now()
    });
    return true;
  } catch (error) {
    console.error('[CoverCache] Error setting Bangumi info:', error.message);
    return false;
  }
}

/**
 * Get cached covers for multiple anime
 */
export function getCachedCovers(animeIds) {
  const result = {};
  try {
    const store = getStore();
    const covers = store.get('covers') || {};
    
    for (const id of animeIds) {
      const data = covers[id];
      if (data && data.cover_url && Date.now() - data.cached_at < CACHE_TTL) {
        result[id] = data;
      }
    }
  } catch (error) {
    console.error('[CoverCache] Error getting covers:', error.message);
  }
  return result;
}

/**
 * Set cached cover for an anime
 */
export function setCachedCover(animeId, title, coverUrl, extraData = {}) {
  try {
    const store = getStore();
    const coverData = {
      cover_url: coverUrl,
      title,
      cached_at: Date.now(),
      ...extraData
    };
    
    store.set(`covers.${animeId}`, coverData);
    return true;
  } catch (error) {
    console.error('[CoverCache] Error setting cover:', error.message);
    return false;
  }
}

/**
 * Set cached covers for multiple anime
 */
export function setCachedCovers(covers) {
  let count = 0;
  try {
    const store = getStore();
    const existing = store.get('covers') || {};
    
    for (const item of covers) {
      existing[item.id] = {
        cover_url: item.cover_url,
        title: item.title,
        cached_at: Date.now()
      };
      count++;
    }
    
    store.set('covers', existing);
  } catch (error) {
    console.error('[CoverCache] Error setting covers:', error.message);
  }
  return count;
}

/**
 * Get cache statistics
 */
export function getCacheStats() {
  try {
    const store = getStore();
    const covers = store.get('covers') || {};
    return { count: Object.keys(covers).length };
  } catch (error) {
    return { count: 0 };
  }
}

export function initCoverCache() {
  // Just ensure store is initialized
  getStore();
  console.log('[CoverCache] Initialized');
}

/**
 * Clear all cover cache
 */
export function clearAllCovers() {
  try {
    const store = getStore();
    const covers = store.get('covers') || {};
    const count = Object.keys(covers).length;
    store.set('covers', {});
    console.log(`[CoverCache] Cleared ${count} covers`);
    return count;
  } catch (error) {
    console.error('[CoverCache] Error clearing covers:', error.message);
    return 0;
  }
}

export default {
  initCoverCache,
  getCachedCover,
  getCachedCovers,
  setCachedCover,
  setCachedCovers,
  getCacheStats,
  getCachedBangumiInfo,
  setCachedBangumiInfo,
  clearAllCovers
};
