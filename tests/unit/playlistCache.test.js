import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock electron-store
const mockStore = {
  data: {},
  get(key) {
    const keys = key.split('.');
    let value = this.data;
    for (const k of keys) {
      if (value === null || value === undefined) return undefined;
      value = value[k];
    }
    return value;
  },
  set(key, value) {
    if (typeof key === 'object') {
      Object.assign(this.data, key);
      return;
    }
    const keys = key.split('.');
    let target = this.data;
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      if (!target[k] || typeof target[k] !== 'object') {
        target[k] = {};
      }
      target = target[k];
    }
    target[keys[keys.length - 1]] = value;
  },
  clear() {
    this.data = {};
  }
};

vi.mock('electron-store', () => {
  return {
    default: class MockStore {
      constructor() {
        return mockStore;
      }
    }
  };
});

describe('Playlist Cache Service', () => {
  beforeEach(() => {
    // Reset mock store
    mockStore.data = {
      animeList: null,
      animeDetails: {},
      episodes: {},
      version: 1
    };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Anime List Cache', () => {
    it('should cache and retrieve anime list', async () => {
      const { setCachedAnimeList, getCachedAnimeList } = await import('../../src/services/playlistCache.js');
      
      const animeList = [
        { id: '1', title: 'Test Anime 1' },
        { id: '2', title: 'Test Anime 2' }
      ];
      
      setCachedAnimeList(animeList);
      const cached = getCachedAnimeList();
      
      expect(cached).toEqual(animeList);
    });

    it('should return null for expired cache', async () => {
      const { setCachedAnimeList, getCachedAnimeList } = await import('../../src/services/playlistCache.js');
      
      const animeList = [{ id: '1', title: 'Test Anime' }];
      setCachedAnimeList(animeList);
      
      // Simulate time passing beyond TTL (5 minutes)
      const originalNow = Date.now;
      Date.now = vi.fn(() => originalNow() + 6 * 60 * 1000);
      
      const cached = getCachedAnimeList();
      expect(cached).toBeNull();
      
      Date.now = originalNow;
    });

    it('should return null when cache is empty', async () => {
      const { getCachedAnimeList } = await import('../../src/services/playlistCache.js');
      
      const cached = getCachedAnimeList();
      expect(cached).toBeNull();
    });

    it('should invalidate anime list cache', async () => {
      const { setCachedAnimeList, getCachedAnimeList, invalidateAnimeList } = await import('../../src/services/playlistCache.js');
      
      const animeList = [{ id: '1', title: 'Test Anime' }];
      setCachedAnimeList(animeList);
      
      invalidateAnimeList();
      
      const cached = getCachedAnimeList();
      expect(cached).toBeNull();
    });
  });

  describe('Anime Detail Cache', () => {
    it('should cache and retrieve anime detail', async () => {
      const { setCachedAnimeDetail, getCachedAnimeDetail } = await import('../../src/services/playlistCache.js');
      
      const animeId = '123';
      const detail = {
        id: animeId,
        title: 'Test Anime',
        description: 'A test anime',
        year: '2024'
      };
      
      setCachedAnimeDetail(animeId, detail);
      const cached = getCachedAnimeDetail(animeId);
      
      expect(cached).toEqual(detail);
    });

    it('should return null for non-existent detail', async () => {
      const { getCachedAnimeDetail } = await import('../../src/services/playlistCache.js');
      
      const cached = getCachedAnimeDetail('999');
      expect(cached).toBeNull();
    });

    it('should invalidate specific anime detail', async () => {
      const { setCachedAnimeDetail, getCachedAnimeDetail, invalidateAnimeDetail } = await import('../../src/services/playlistCache.js');
      
      setCachedAnimeDetail('123', { title: 'Anime 1' });
      setCachedAnimeDetail('456', { title: 'Anime 2' });
      
      invalidateAnimeDetail('123');
      
      expect(getCachedAnimeDetail('123')).toBeNull();
      expect(getCachedAnimeDetail('456')).toEqual({ title: 'Anime 2' });
    });
  });

  describe('Episodes Cache', () => {
    it('should cache and retrieve episodes', async () => {
      const { setCachedEpisodes, getCachedEpisodes } = await import('../../src/services/playlistCache.js');
      
      const animeId = '123';
      const episodes = [
        { id: '1', title: 'Episode 1', episode: '1' },
        { id: '2', title: 'Episode 2', episode: '2' }
      ];
      
      setCachedEpisodes(animeId, episodes);
      const cached = getCachedEpisodes(animeId);
      
      expect(cached).toEqual(episodes);
    });

    it('should invalidate episodes cache', async () => {
      const { setCachedEpisodes, getCachedEpisodes, invalidateEpisodes } = await import('../../src/services/playlistCache.js');
      
      const animeId = '123';
      setCachedEpisodes(animeId, [{ id: '1', title: 'Episode 1' }]);
      
      invalidateEpisodes(animeId);
      
      const cached = getCachedEpisodes(animeId);
      expect(cached).toBeNull();
    });
  });

  describe('Cache Statistics', () => {
    it('should return cache statistics', async () => {
      const { 
        setCachedAnimeList, 
        setCachedAnimeDetail, 
        setCachedEpisodes,
        getCacheStats 
      } = await import('../../src/services/playlistCache.js');
      
      setCachedAnimeList([{ id: '1' }, { id: '2' }]);
      setCachedAnimeDetail('123', { title: 'Test' });
      setCachedEpisodes('123', [{ id: '1' }]);
      
      const stats = getCacheStats();
      
      expect(stats).toBeTruthy();
      expect(stats.animeList.cached).toBe(true);
      expect(stats.animeList.itemCount).toBe(2);
      expect(stats.animeDetails.count).toBe(1);
      expect(stats.episodes.count).toBe(1);
    });

    it('should include TTL information in stats', async () => {
      const { getCacheStats } = await import('../../src/services/playlistCache.js');
      
      const stats = getCacheStats();
      
      expect(stats.ttl).toBeTruthy();
      expect(stats.ttl.animeList).toBeGreaterThan(0);
      expect(stats.ttl.animeDetail).toBeGreaterThan(0);
      expect(stats.ttl.episodes).toBeGreaterThan(0);
    });

    it('should count valid and invalid cache entries', async () => {
      const { setCachedAnimeDetail, getCacheStats } = await import('../../src/services/playlistCache.js');
      
      const originalNow = Date.now;
      const baseTime = originalNow();
      
      // Set entries at base time
      setCachedAnimeDetail('123', { title: 'Expired 1' });
      setCachedAnimeDetail('456', { title: 'Expired 2' });
      
      // Move time forward beyond TTL (30 minutes for anime detail)
      Date.now = vi.fn(() => baseTime + 31 * 60 * 1000);
      
      // Add a new entry at the new time (this one is valid)
      setCachedAnimeDetail('789', { title: 'Still Valid' });
      
      const stats = getCacheStats();
      expect(stats.animeDetails.count).toBe(3);
      expect(stats.animeDetails.validCount).toBe(1); // Only '789' is valid
      
      Date.now = originalNow;
    });
  });

  describe('Cache Cleanup', () => {
    it('should clear all cache', async () => {
      const { 
        setCachedAnimeList, 
        setCachedAnimeDetail, 
        setCachedEpisodes,
        getCachedAnimeList,
        getCachedAnimeDetail,
        getCachedEpisodes,
        clearAllCache 
      } = await import('../../src/services/playlistCache.js');
      
      setCachedAnimeList([{ id: '1' }]);
      setCachedAnimeDetail('123', { title: 'Test' });
      setCachedEpisodes('123', [{ id: '1' }]);
      
      const stats = clearAllCache();
      
      expect(stats).toBeTruthy();
      expect(getCachedAnimeList()).toBeNull();
      expect(getCachedAnimeDetail('123')).toBeNull();
      expect(getCachedEpisodes('123')).toBeNull();
    });

    it('should clear expired entries only', async () => {
      const { 
        setCachedAnimeDetail,
        getCachedAnimeDetail,
        clearExpiredCache 
      } = await import('../../src/services/playlistCache.js');
      
      const originalNow = Date.now;
      
      // Add entry at current time
      setCachedAnimeDetail('123', { title: 'Will Expire' });
      
      // Move time forward beyond TTL
      Date.now = vi.fn(() => originalNow() + 31 * 60 * 1000);
      
      // Add another entry at the new time
      setCachedAnimeDetail('456', { title: 'Still Valid' });
      
      // Clear expired entries
      const cleared = clearExpiredCache();
      
      expect(cleared.clearedDetails).toBe(1);
      expect(getCachedAnimeDetail('123')).toBeNull();
      expect(getCachedAnimeDetail('456')).toEqual({ title: 'Still Valid' });
      
      Date.now = originalNow;
    });
  });

  describe('Error Handling', () => {
    it('should handle errors gracefully when setting cache', async () => {
      const { setCachedAnimeList } = await import('../../src/services/playlistCache.js');
      
      // Mock store to throw error
      const originalSet = mockStore.set;
      mockStore.set = vi.fn(() => {
        throw new Error('Store error');
      });
      
      const result = setCachedAnimeList([{ id: '1' }]);
      expect(result).toBe(false);
      
      mockStore.set = originalSet;
    });

    it('should handle errors gracefully when getting cache', async () => {
      const { getCachedAnimeList } = await import('../../src/services/playlistCache.js');
      
      // Mock store to throw error
      const originalGet = mockStore.get;
      mockStore.get = vi.fn(() => {
        throw new Error('Store error');
      });
      
      const result = getCachedAnimeList();
      expect(result).toBeNull();
      
      mockStore.get = originalGet;
    });
  });
});
