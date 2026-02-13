import Store from 'electron-store';

const store = new Store({
  name: 'anime1-data',
  defaults: {
    favorites: [],
    playbackHistory: [],
    settings: {
      theme: 'system'
    }
  }
});

// Cover cache store (separate from main store)
const coverStore = new Store({
  name: 'cover-cache',
  defaults: {
    covers: {}
  }
});

// Favorites operations
export const favoritesDB = {
  async list() {
    return store.get('favorites') || [];
  },
  
  async add(anime) {
    const favorites = await this.list();
    const exists = favorites.some(f => f.id === anime.id);
    if (!exists) {
      favorites.push({
        ...anime,
        createdAt: new Date().toISOString()
      });
      store.set('favorites', favorites);
    }
    return { success: true };
  },
  
  async remove(animeId) {
    const favorites = await this.list();
    const filtered = favorites.filter(f => f.id !== animeId);
    store.set('favorites', filtered);
    return { success: true };
  },
  
  async isFavorite(animeId) {
    const favorites = await this.list();
    return favorites.some(f => f.id === animeId);
  }
};

// Playback history operations
export const playbackDB = {
  async list(limit = 50) {
    const history = store.get('playbackHistory') || [];
    return history.slice(0, limit);
  },
  
  async update(data) {
    const history = store.get('playbackHistory') || [];
    
    // Remove existing entry for same anime/episode
    const filtered = history.filter(h => 
      !(h.animeId === data.animeId && h.episodeId === data.episodeId)
    );
    
    // Add new entry at beginning
    filtered.unshift({
      ...data,
      playedAt: new Date().toISOString()
    });
    
    // Keep only last 100 entries
    store.set('playbackHistory', filtered.slice(0, 100));
    return { success: true };
  },
  
  async getEpisodeProgress(animeId, episodeId) {
    const history = await this.list(100);
    return history.find(h => h.animeId === animeId && h.episodeId === episodeId) || null;
  },
  
  clearAll() {
    const count = (store.get('playbackHistory') || []).length;
    store.set('playbackHistory', []);
    console.log(`[PlaybackDB] Cleared ${count} history entries`);
    return count;
  }
};

// Settings operations
export const settingsDB = {
  async get(key) {
    const settings = store.get('settings') || {};
    return settings[key] || null;
  },
  
  async set(key, value) {
    const settings = store.get('settings') || {};
    settings[key] = value;
    store.set('settings', settings);
    return { success: true };
  }
};

// Cache operations
export const cacheDB = {
  async getInfo() {
    // Get cover cache info from cover-cache store
    const covers = coverStore.get('covers') || {};
    const coverCount = Object.keys(covers).length;
    
    // Calculate size
    const size = JSON.stringify(covers).length;
    
    // Format size to human readable
    let sizeFormatted = '0 B';
    if (size > 0) {
      const units = ['B', 'KB', 'MB', 'GB'];
      let unitIndex = 0;
      let sizeValue = size;
      while (sizeValue >= 1024 && unitIndex < units.length - 1) {
        sizeValue /= 1024;
        unitIndex++;
      }
      sizeFormatted = `${sizeValue.toFixed(1)} ${units[unitIndex]}`;
    }
    
    return { 
      cover_count: coverCount, 
      database_size: size,
      database_size_formatted: sizeFormatted
    };
  },
  
  async clear(type = 'all') {
    switch (type) {
      case 'covers':
        // Clear cover cache from store
        console.log('[Cache] Clearing cover cache');
        store.set('covers', {});
        break;
      case 'favorites':
        store.set('favorites', []);
        break;
      case 'playback':
        store.set('playbackHistory', []);
        break;
      case 'all':
        store.clear();
        break;
      default:
        return { success: false, error: 'Unknown cache type' };
    }
    return { success: true };
  }
};

// Initialize (no-op for electron-store)
export async function initDatabase() {
  console.log('[Database] Initialized with electron-store');
  return true;
}

export function getDatabase() {
  return store;
}
