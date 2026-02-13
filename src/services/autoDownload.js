/**
 * Auto Download Service
 * 
 * Features:
 * - Download configuration with filters
 * - Download task management with VideoDownloader
 * - Download history tracking
 * - Background scheduler (Node.js setInterval)
 */

import { app } from 'electron';
import path from 'path';
import fs from 'fs';
import { settingsDB } from './database.js';
import { getVideoDownloader, DownloadStatus } from './videoDownloader.js';
import { getVideoInfo } from './videoProxy.js';

// Export DownloadStatus for compatibility
export { DownloadStatus };

// Default download config
const DEFAULT_CONFIG = {
  enabled: false,
  downloadPath: '',
  checkIntervalHours: 24,
  maxConcurrentDownloads: 2,
  autoDownloadNew: false,
  autoDownloadFavorites: true,
  filters: {
    minYear: null,
    maxYear: null,
    specificYears: [],
    seasons: [], // ['冬季', '春季', '夏季', '秋季']
    minEpisodes: null,
    includePatterns: [],
    excludePatterns: [],
  }
};

class AutoDownloadService {
  constructor() {
    this._config = null;
    this._history = [];
    this._schedulerInterval = null;
    this._isRunning = false;
    this._downloadCallbacks = [];
    this._videoDownloader = null;
    this._webContents = null; // For sending events to renderer
  }

  /**
   * Set WebContents for sending events to renderer
   */
  setWebContents(webContents) {
    this._webContents = webContents;
  }

  /**
   * Initialize the service
   */
  async init() {
    await this._loadConfig();
    await this._loadHistory();
    
    // Ensure config is initialized
    if (!this._config) {
      this._config = { ...DEFAULT_CONFIG };
    }
    
    // Initialize video downloader
    this._initVideoDownloader();
    
    // Start scheduler if enabled
    if (this._config.enabled) {
      this.startScheduler();
    }
  }

  /**
   * Initialize video downloader
   */
  _initVideoDownloader() {
    const downloadPath = this.getDownloadPath();
    const maxConcurrent = this._config?.maxConcurrentDownloads || 2;
    
    this._videoDownloader = getVideoDownloader(downloadPath, maxConcurrent);
    
    // Register event handlers
    this._videoDownloader.on('started', (progress) => {
      this._updateDownloadRecord(progress.episodeId, {
        status: DownloadStatus.DOWNLOADING,
        progress: 0,
      });
      this._notifyRenderer('download-started', progress);
    });
    
    this._videoDownloader.on('progress', (progress) => {
      this._updateDownloadRecord(progress.episodeId, {
        status: DownloadStatus.DOWNLOADING,
        progress: progress.percent,
        totalBytes: progress.totalBytes,
        downloadedBytes: progress.downloadedBytes,
        speedBytesPerSec: progress.speedBytesPerSec,
      });
      this._notifyRenderer('download-progress', progress);
    });
    
    this._videoDownloader.on('completed', (progress) => {
      this._updateDownloadRecord(progress.episodeId, {
        status: DownloadStatus.COMPLETED,
        progress: 100,
        filePath: progress.filePath,
        completedAt: new Date().toISOString(),
      });
      this._notifyRenderer('download-completed', progress);
    });
    
    this._videoDownloader.on('error', (progress) => {
      this._updateDownloadRecord(progress.episodeId, {
        status: DownloadStatus.FAILED,
        errorMessage: progress.errorMessage,
        completedAt: new Date().toISOString(),
      });
      this._notifyRenderer('download-error', progress);
    });
    
    this._videoDownloader.on('cancelled', (progress) => {
      this._updateDownloadRecord(progress.episodeId, {
        status: DownloadStatus.CANCELLED,
        completedAt: new Date().toISOString(),
      });
      this._notifyRenderer('download-cancelled', progress);
    });
  }

  /**
   * Notify renderer process of download events
   */
  _notifyRenderer(event, data) {
    // Call registered callbacks
    for (const callback of this._downloadCallbacks) {
      try {
        callback(event, data);
      } catch (error) {
        console.error('[AutoDownload] Callback error:', error);
      }
    }
    
    // Send to renderer via WebContents
    if (this._webContents && !this._webContents.isDestroyed()) {
      this._webContents.send('auto-download:' + event, data);
    }
  }

  /**
   * Update download record in history
   */
  _updateDownloadRecord(episodeId, updates) {
    const record = this._history.find(r => r.episodeId === episodeId);
    if (record) {
      Object.assign(record, updates);
      this._saveHistory();
    }
  }

  /**
   * Get download directory
   */
  getDownloadPath() {
    const config = this._config || DEFAULT_CONFIG;
    if (config.downloadPath) {
      const dir = config.downloadPath;
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      return dir;
    }
    
    // Default to Downloads/Anime1
    const downloadsPath = path.join(app.getPath('downloads'), 'Anime1');
    if (!fs.existsSync(downloadsPath)) {
      fs.mkdirSync(downloadsPath, { recursive: true });
    }
    return downloadsPath;
  }

  /**
   * Load config from database
   */
  async _loadConfig() {
    try {
      const saved = await settingsDB.get('autoDownloadConfig');
      this._config = saved ? { ...DEFAULT_CONFIG, ...saved } : { ...DEFAULT_CONFIG };
    } catch (error) {
      console.error('[AutoDownload] Error loading config:', error);
      this._config = { ...DEFAULT_CONFIG };
    }
  }

  /**
   * Save config to database
   */
  async _saveConfig() {
    try {
      await settingsDB.set('autoDownloadConfig', this._config);
    } catch (error) {
      console.error('[AutoDownload] Error saving config:', error);
    }
  }

  /**
   * Load download history from database
   */
  async _loadHistory() {
    try {
      const saved = await settingsDB.get('autoDownloadHistory');
      this._history = saved || [];
    } catch (error) {
      console.error('[AutoDownload] Error loading history:', error);
      this._history = [];
    }
  }

  /**
   * Save download history to database
   */
  async _saveHistory() {
    try {
      // Keep only last 1000 records
      const trimmedHistory = this._history.slice(-1000);
      await settingsDB.set('autoDownloadHistory', trimmedHistory);
    } catch (error) {
      console.error('[AutoDownload] Error saving history:', error);
    }
  }

  /**
   * Get current config
   */
  getConfig() {
    return { ...(this._config || DEFAULT_CONFIG) };
  }

  /**
   * Update config
   */
  async updateConfig(newConfig) {
    this._config = { ...(this._config || DEFAULT_CONFIG), ...newConfig };
    await this._saveConfig();
    
    // Update video downloader settings
    if (this._videoDownloader) {
      // Recreate with new settings if max concurrent changed
      const maxConcurrent = this._config.maxConcurrentDownloads || 2;
      // Note: maxConcurrent is set at creation, would need to recreate to change
    }
    
    // Restart scheduler if running state changed
    const config = this._config || DEFAULT_CONFIG;
    if (config.enabled && !this._isRunning) {
      this.startScheduler();
    } else if (!config.enabled && this._isRunning) {
      this.stopScheduler();
    }
    
    return true;
  }

  /**
   * Get download history
   */
  getHistory(limit = 50, status = null) {
    let history = [...this._history];
    
    if (status) {
      history = history.filter(r => r.status === status);
    }
    
    // Sort by createdAt desc
    history.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
    return history.slice(0, limit);
  }
  
  /**
   * Get all downloads
   */
  getAllDownloads() {
    return [...this._history];
  }

  /**
   * Get active downloads
   */
  getActiveDownloads() {
    if (!this._videoDownloader) return [];
    return this._videoDownloader.getActiveDownloads();
  }

  /**
   * Check if anime matches filters
   */
  matchesFilters(anime) {
    if (!this._config || !this._config.filters) {
      return true; // If config not loaded, allow all
    }
    const filters = this._config.filters;
    
    // Year filter
    if (anime.year && filters.minYear) {
      const year = parseInt(anime.year);
      if (!isNaN(year) && year < filters.minYear) return false;
    }
    if (anime.year && filters.maxYear) {
      const year = parseInt(anime.year);
      if (!isNaN(year) && year > filters.maxYear) return false;
    }
    if (filters.specificYears?.length > 0 && anime.year) {
      const year = parseInt(anime.year);
      if (!filters.specificYears.includes(year)) return false;
    }
    
    // Season filter
    if (filters.seasons?.length > 0 && anime.season) {
      if (!filters.seasons.includes(anime.season)) return false;
    }
    
    // Episode filter
    if (filters.minEpisodes && anime.episode) {
      const ep = parseInt(anime.episode);
      if (!isNaN(ep) && ep < filters.minEpisodes) return false;
    }
    
    // Include patterns
    if (filters.includePatterns?.length > 0 && anime.title) {
      const matched = filters.includePatterns.some(pattern => {
        try {
          const regex = new RegExp(pattern, 'i');
          return regex.test(anime.title);
        } catch {
          return anime.title.includes(pattern);
        }
      });
      if (!matched) return false;
    }
    
    // Exclude patterns
    if (filters.excludePatterns?.length > 0 && anime.title) {
      const excluded = filters.excludePatterns.some(pattern => {
        try {
          const regex = new RegExp(pattern, 'i');
          return regex.test(anime.title);
        } catch {
          return anime.title.includes(pattern);
        }
      });
      if (excluded) return false;
    }
    
    return true;
  }

  /**
   * Start the background scheduler
   */
  startScheduler() {
    if (this._isRunning) {
      console.log('[AutoDownload] Scheduler already running');
      return;
    }
    
    const config = this._config || DEFAULT_CONFIG;
    if (!config.enabled) {
      console.log('[AutoDownload] Not starting scheduler (disabled)');
      return;
    }
    
    this._isRunning = true;
    console.log('[AutoDownload] Scheduler started');
    
    // Run immediately, then schedule
    this._checkAndDownload();
    
    // Schedule next check
    const intervalMs = config.checkIntervalHours * 60 * 60 * 1000;
    this._schedulerInterval = setInterval(() => {
      this._checkAndDownload();
    }, intervalMs);
  }

  /**
   * Stop the scheduler
   */
  stopScheduler() {
    if (!this._isRunning) return;
    
    if (this._schedulerInterval) {
      clearInterval(this._schedulerInterval);
      this._schedulerInterval = null;
    }
    
    this._isRunning = false;
    console.log('[AutoDownload] Scheduler stopped');
  }

  /**
   * Check for new episodes and download
   */
  async _checkAndDownload() {
    console.log('[AutoDownload] Running scheduled check...');
    
    try {
      // This will be implemented to check favorites and new anime
      // For now, just log that check ran
      console.log('[AutoDownload] Check completed');
    } catch (error) {
      console.error('[AutoDownload] Error during check:', error);
    }
  }

  /**
   * Start a new download
   */
  async startDownload(anime, episode, videoUrl = null, cookies = null) {
    const episodeId = episode.id;
    
    // Check if already downloaded
    const existing = this._history.find(r => 
      r.episodeId === episodeId && r.status === DownloadStatus.COMPLETED
    );
    if (existing) {
      throw new Error('Episode already downloaded');
    }

    // If no videoUrl provided, fetch it
    let finalVideoUrl = videoUrl;
    let finalCookies = cookies || {};
    
    if (!finalVideoUrl) {
      const videoInfo = await getVideoInfo(episode.url);
      if (!videoInfo.success) {
        throw new Error(videoInfo.error || 'Failed to get video info');
      }
      finalVideoUrl = videoInfo.url;
      finalCookies = videoInfo.cookies || {};
    }

    // Create download record
    const record = {
      id: `${anime.id}_${episodeId}`,
      animeId: anime.id,
      animeTitle: anime.title,
      episodeId: episodeId,
      episodeNum: episode.episode || episode.title,
      status: DownloadStatus.PENDING,
      progress: 0,
      totalBytes: 0,
      downloadedBytes: 0,
      filePath: '',
      errorMessage: '',
      createdAt: new Date().toISOString(),
      completedAt: null,
    };
    
    this._history.push(record);
    await this._saveHistory();
    
    // Add to video downloader
    try {
      const progress = await this._videoDownloader.addDownload(
        anime,
        episode,
        finalVideoUrl,
        finalCookies
      );
      
      // Update record with initial progress
      Object.assign(record, {
        status: progress.status,
        totalBytes: progress.totalBytes,
        downloadedBytes: progress.downloadedBytes,
      });
      await this._saveHistory();
      
      return record;
    } catch (error) {
      // Update record with error
      record.status = DownloadStatus.FAILED;
      record.errorMessage = error.message;
      record.completedAt = new Date().toISOString();
      await this._saveHistory();
      throw error;
    }
  }

  /**
   * Cancel a download
   */
  async cancelDownload(episodeId) {
    if (!this._videoDownloader) {
      throw new Error('Video downloader not initialized');
    }
    
    const result = this._videoDownloader.cancelDownload(episodeId);
    
    // Update record
    const record = this._history.find(r => r.episodeId === episodeId);
    if (record) {
      record.status = DownloadStatus.CANCELLED;
      record.completedAt = new Date().toISOString();
      await this._saveHistory();
    }
    
    return result;
  }

  /**
   * Delete a download record and file
   */
  async deleteDownload(downloadId) {
    const index = this._history.findIndex(r => r.id === downloadId);
    if (index === -1) {
      throw new Error('Download record not found');
    }
    
    const record = this._history[index];
    
    // Delete file if exists
    if (record.filePath && fs.existsSync(record.filePath)) {
      try {
        fs.unlinkSync(record.filePath);
      } catch (error) {
        console.error('[AutoDownload] Error deleting file:', error);
      }
    }
    
    // Remove from history
    this._history.splice(index, 1);
    await this._saveHistory();
    
    return true;
  }

  /**
   * Get service status
   */
  getStatus() {
    const statusCounts = {
      pending: 0,
      downloading: 0,
      completed: 0,
      failed: 0,
      cancelled: 0,
    };
    
    for (const record of this._history) {
      statusCounts[record.status] = (statusCounts[record.status] || 0) + 1;
    }
    
    const config = this._config || DEFAULT_CONFIG;
    
    return {
      enabled: config.enabled,
      running: this._isRunning,
      downloadPath: this.getDownloadPath(),
      checkIntervalHours: config.checkIntervalHours,
      maxConcurrentDownloads: config.maxConcurrentDownloads,
      activeDownloads: this.getActiveDownloads().length,
      statusCounts,
      recentDownloads: this.getHistory(10),
    };
  }

  /**
   * Preview filter results on anime list
   */
  previewFilter(animeList) {
    return animeList.filter(anime => this.matchesFilters(anime));
  }

  /**
   * Register download callback
   */
  onDownload(callback) {
    this._downloadCallbacks.push(callback);
  }

  /**
   * Unregister download callback
   */
  offDownload(callback) {
    const index = this._downloadCallbacks.indexOf(callback);
    if (index > -1) {
      this._downloadCallbacks.splice(index, 1);
    }
  }

  /**
   * Clear completed downloads from memory
   */
  clearCompletedDownloads() {
    if (this._videoDownloader) {
      this._videoDownloader.clearCompleted();
    }
  }

  /**
   * Destroy service
   */
  destroy() {
    this.stopScheduler();
    
    if (this._videoDownloader) {
      this._videoDownloader.destroy();
      this._videoDownloader = null;
    }
    
    this._downloadCallbacks = [];
  }
}

// Singleton instance
let autoDownloadService = null;

export function getAutoDownloadService() {
  if (!autoDownloadService) {
    autoDownloadService = new AutoDownloadService();
  }
  return autoDownloadService;
}

export function resetAutoDownloadService() {
  if (autoDownloadService) {
    autoDownloadService.destroy();
    autoDownloadService = null;
  }
}

export default {
  getAutoDownloadService,
  resetAutoDownloadService,
  DownloadStatus,
};
