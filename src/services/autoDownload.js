/**
 * Auto Download Service
 * 
 * Features:
 * - Download configuration with filters
 * - Download task management
 * - Download history tracking
 * - Background scheduler (Node.js setInterval)
 */

import { app } from 'electron';
import path from 'path';
import fs from 'fs';
import axios from 'axios';
import { settingsDB } from './database.js';

// Download status enum
export const DownloadStatus = {
  PENDING: 'pending',
  DOWNLOADING: 'downloading',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

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

// Download record type
// {
//   id: string,
//   animeId: string,
//   animeTitle: string,
//   episodeId: string,
//   episodeNum: string,
//   status: DownloadStatus,
//   progress: number,
//   totalBytes: number,
//   downloadedBytes: number,
//   filePath: string,
//   errorMessage: string,
//   createdAt: string,
//   completedAt: string,
// }

class AutoDownloadService {
  constructor() {
    this._config = null;
    this._history = [];
    this._activeDownloads = new Map();
    this._schedulerInterval = null;
    this._isRunning = false;
    this._downloadCallbacks = [];
  }

  /**
   * Initialize the service
   */
  async init() {
    await this._loadConfig();
    await this._loadHistory();
    
    // Start scheduler if enabled
    if (this._config.enabled) {
      this.startScheduler();
    }
  }

  /**
   * Get download directory
   */
  getDownloadPath() {
    if (this._config?.downloadPath) {
      const dir = this._config.downloadPath;
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
      await settingsDB.set('autoDownloadHistory', this._history);
    } catch (error) {
      console.error('[AutoDownload] Error saving history:', error);
    }
  }

  /**
   * Get current config
   */
  getConfig() {
    return { ...this._config };
  }

  /**
   * Update config
   */
  async updateConfig(newConfig) {
    this._config = { ...this._config, ...newConfig };
    await this._saveConfig();
    
    // Restart scheduler if running state changed
    if (this._config.enabled && !this._isRunning) {
      this.startScheduler();
    } else if (!this._config.enabled && this._isRunning) {
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
   * Get active downloads
   */
  getActiveDownloads() {
    return Array.from(this._activeDownloads.values());
  }

  /**
   * Check if anime matches filters
   */
  matchesFilters(anime) {
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
    
    if (!this._config.enabled) {
      console.log('[AutoDownload] Not starting scheduler (disabled)');
      return;
    }
    
    this._isRunning = true;
    console.log('[AutoDownload] Scheduler started');
    
    // Run immediately, then schedule
    this._checkAndDownload();
    
    // Schedule next check
    const intervalMs = this._config.checkIntervalHours * 60 * 60 * 1000;
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
  async startDownload(anime, episode, videoUrl) {
    const downloadId = `${anime.id}_${episode.id}`;
    
    // Check if already downloading
    if (this._activeDownloads.has(downloadId)) {
      throw new Error('Download already in progress');
    }
    
    // Check if already downloaded
    const existing = this._history.find(r => r.episodeId === episode.id && r.status === DownloadStatus.COMPLETED);
    if (existing) {
      throw new Error('Episode already downloaded');
    }
    
    // Create download record
    const record = {
      id: downloadId,
      animeId: anime.id,
      animeTitle: anime.title,
      episodeId: episode.id,
      episodeNum: episode.episode || episode.title,
      status: DownloadStatus.DOWNLOADING,
      progress: 0,
      totalBytes: 0,
      downloadedBytes: 0,
      filePath: '',
      errorMessage: '',
      createdAt: new Date().toISOString(),
      completedAt: null,
    };
    
    this._activeDownloads.set(downloadId, record);
    this._history.push(record);
    await this._saveHistory();
    
    // Start download
    this._downloadFile(downloadId, videoUrl).catch(error => {
      console.error('[AutoDownload] Download error:', error);
      record.status = DownloadStatus.FAILED;
      record.errorMessage = error.message;
      this._activeDownloads.delete(downloadId);
      this._saveHistory();
    });
    
    return record;
  }

  /**
   * Download file using axios stream
   */
  async _downloadFile(downloadId, videoUrl) {
    const record = this._activeDownloads.get(downloadId);
    if (!record) return;
    
    try {
      // Determine file extension
      const ext = videoUrl.includes('.m3u8') ? '.mp4' : path.extname(new URL(videoUrl).pathname) || '.mp4';
      const fileName = `${record.animeTitle}_EP${record.episodeNum}_${Date.now()}${ext}`;
      const filePath = path.join(this.getDownloadPath(), fileName);
      
      record.filePath = filePath;
      
      // Download with axios stream
      const response = await axios({
        method: 'GET',
        url: videoUrl,
        responseType: 'stream',
        timeout: 300000, // 5 minutes
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total) {
            record.totalBytes = progressEvent.total;
            record.downloadedBytes = progressEvent.loaded;
            record.progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
            
            // Notify callbacks
            this._notifyCallbacks('progress', record);
          }
        }
      });
      
      // Write to file
      const writer = fs.createWriteStream(filePath);
      response.data.pipe(writer);
      
      await new Promise((resolve, reject) => {
        writer.on('finish', resolve);
        writer.on('error', reject);
      });
      
      // Update record
      record.status = DownloadStatus.COMPLETED;
      record.progress = 100;
      record.completedAt = new Date().toISOString();
      
      console.log('[AutoDownload] Download completed:', filePath);
      
      // Notify callbacks
      this._notifyCallbacks('completed', record);
      
    } catch (error) {
      record.status = DownloadStatus.FAILED;
      record.errorMessage = error.message;
      this._notifyCallbacks('error', record);
      throw error;
    } finally {
      this._activeDownloads.delete(downloadId);
      await this._saveHistory();
    }
  }

  /**
   * Cancel a download
   */
  async cancelDownload(downloadId) {
    const record = this._activeDownloads.get(downloadId);
    if (!record) {
      throw new Error('Download not found');
    }
    
    record.status = DownloadStatus.CANCELLED;
    this._activeDownloads.delete(downloadId);
    await this._saveHistory();
    
    this._notifyCallbacks('cancelled', record);
    return record;
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
      fs.unlinkSync(record.filePath);
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
    
    return {
      enabled: this._config.enabled,
      running: this._isRunning,
      downloadPath: this.getDownloadPath(),
      checkIntervalHours: this._config.checkIntervalHours,
      maxConcurrentDownloads: this._config.maxConcurrentDownloads,
      activeDownloads: this._activeDownloads.size,
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
   * Notify callbacks
   */
  _notifyCallbacks(event, record) {
    for (const callback of this._downloadCallbacks) {
      try {
        callback(event, record);
      } catch (error) {
        console.error('[AutoDownload] Callback error:', error);
      }
    }
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

export default getAutoDownloadService;
