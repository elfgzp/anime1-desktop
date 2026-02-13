/**
 * Video Downloader Service for Electron
 * 
 * Features:
 * - Async download with progress tracking
 * - Resume partial downloads
 * - Concurrent download limiting
 * - Download queue management
 * - Speed calculation
 */

import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';

// Download status enum
export const DownloadStatus = {
  PENDING: 'pending',
  DOWNLOADING: 'downloading',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  PAUSED: 'paused',
};

/**
 * Download progress information
 */
export class DownloadProgress {
  constructor(episodeId) {
    this.episodeId = episodeId;
    this.totalBytes = 0;
    this.downloadedBytes = 0;
    this.speedBytesPerSec = 0;
    this.status = DownloadStatus.PENDING;
    this.errorMessage = null;
    this.startTime = null;
    this.endTime = null;
    this.filePath = null;
    this.lastUpdateTime = null;
    this.lastDownloadedBytes = 0;
  }

  get percent() {
    if (this.totalBytes === 0) return 0;
    return (this.downloadedBytes / this.totalBytes) * 100;
  }

  get elapsedSeconds() {
    if (!this.startTime) return 0;
    const end = this.endTime || Date.now();
    return (end - this.startTime) / 1000;
  }

  updateSpeed() {
    const now = Date.now();
    if (!this.lastUpdateTime) {
      this.lastUpdateTime = now;
      this.lastDownloadedBytes = this.downloadedBytes;
      return;
    }

    const timeDiff = (now - this.lastUpdateTime) / 1000;
    if (timeDiff > 0) {
      const bytesDiff = this.downloadedBytes - this.lastDownloadedBytes;
      this.speedBytesPerSec = bytesDiff / timeDiff;
      this.lastUpdateTime = now;
      this.lastDownloadedBytes = this.downloadedBytes;
    }
  }

  toJSON() {
    return {
      episodeId: this.episodeId,
      totalBytes: this.totalBytes,
      downloadedBytes: this.downloadedBytes,
      speedBytesPerSec: Math.round(this.speedBytesPerSec),
      status: this.status,
      errorMessage: this.errorMessage,
      percent: Math.round(this.percent * 100) / 100,
      elapsedSeconds: Math.round(this.elapsedSeconds * 100) / 100,
      filePath: this.filePath,
    };
  }
}

/**
 * Video Downloader with progress tracking
 */
export class VideoDownloader extends EventEmitter {
  constructor(downloadDir, maxConcurrent = 2) {
    super();
    this.downloadDir = downloadDir;
    this.maxConcurrent = maxConcurrent;
    this.activeDownloads = new Map();
    this.downloadQueue = [];
    this.progressMap = new Map();
    this._checkInterval = null;
    
    // Ensure download directory exists
    if (!fs.existsSync(downloadDir)) {
      fs.mkdirSync(downloadDir, { recursive: true });
    }

    // Start progress update interval
    this._startProgressUpdates();
  }

  /**
   * Start progress update interval
   */
  _startProgressUpdates() {
    this._checkInterval = setInterval(() => {
      this.progressMap.forEach((progress) => {
        if (progress.status === DownloadStatus.DOWNLOADING) {
          progress.updateSpeed();
          this.emit('progress', progress.toJSON());
        }
      });
    }, 1000);
  }

  /**
   * Stop progress updates
   */
  _stopProgressUpdates() {
    if (this._checkInterval) {
      clearInterval(this._checkInterval);
      this._checkInterval = null;
    }
  }

  /**
   * Get safe filename from anime title and episode
   */
  _getSafeFileName(animeTitle, episodeNum, ext = '.mp4') {
    // Remove invalid characters
    const safeTitle = animeTitle.replace(/[<>:"/\\|?*]/g, '_').trim();
    const safeEpisode = String(episodeNum).replace(/[<>:"/\\|?*]/g, '_').trim();
    const timestamp = Date.now();
    return `${safeTitle}_EP${safeEpisode}_${timestamp}${ext}`;
  }

  /**
   * Get file extension from URL
   */
  _getFileExtension(url) {
    if (url.includes('.m3u8')) return '.mp4';
    const match = url.match(/\.([a-zA-Z0-9]+)(?:\?|$)/);
    return match ? `.${match[1].toLowerCase()}` : '.mp4';
  }

  /**
   * Check if download can start (respect max concurrent)
   */
  _canStartDownload() {
    const activeCount = Array.from(this.activeDownloads.values())
      .filter(d => d.status === DownloadStatus.DOWNLOADING).length;
    return activeCount < this.maxConcurrent;
  }

  /**
   * Process download queue
   */
  _processQueue() {
    while (this.downloadQueue.length > 0 && this._canStartDownload()) {
      const item = this.downloadQueue.shift();
      this._startDownload(item);
    }
  }

  /**
   * Add download to queue
   */
  async addDownload(anime, episode, videoUrl, cookies = {}) {
    const episodeId = episode.id;

    // Check if already downloading or completed
    if (this.activeDownloads.has(episodeId)) {
      const existing = this.activeDownloads.get(episodeId);
      if (existing.status === DownloadStatus.DOWNLOADING || 
          existing.status === DownloadStatus.PENDING) {
        throw new Error('Download already in progress');
      }
      if (existing.status === DownloadStatus.COMPLETED) {
        throw new Error('Episode already downloaded');
      }
    }

    // Create download item
    const downloadItem = {
      anime,
      episode,
      videoUrl,
      cookies,
      episodeId,
    };

    // Create progress tracker
    const progress = new DownloadProgress(episodeId);
    progress.status = DownloadStatus.PENDING;
    this.progressMap.set(episodeId, progress);
    this.activeDownloads.set(episodeId, progress);

    // Add to queue or start immediately
    if (this._canStartDownload()) {
      this._startDownload(downloadItem);
    } else {
      this.downloadQueue.push(downloadItem);
      progress.status = DownloadStatus.PENDING;
      this.emit('queued', progress.toJSON());
    }

    return progress.toJSON();
  }

  /**
   * Start actual download
   */
  async _startDownload(item) {
    const { anime, episode, videoUrl, cookies, episodeId } = item;
    const progress = this.progressMap.get(episodeId);
    
    if (!progress) return;

    progress.status = DownloadStatus.DOWNLOADING;
    progress.startTime = Date.now();
    this.emit('started', progress.toJSON());

    // Determine file path
    const ext = this._getFileExtension(videoUrl);
    const fileName = this._getSafeFileName(anime.title, episode.episode || episode.title, ext);
    const filePath = path.join(this.downloadDir, fileName);
    progress.filePath = filePath;

    try {
      // Prepare headers
      const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': 'https://anime1.me',
        'Origin': 'https://anime1.me',
      };

      // Add cookies if provided
      if (Object.keys(cookies).length > 0) {
        const cookieHeader = Object.entries(cookies)
          .map(([name, value]) => `${name}=${value}`)
          .join('; ');
        headers['Cookie'] = cookieHeader;
      }

      // Check for partial download
      let startByte = 0;
      if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        startByte = stats.size;
        progress.downloadedBytes = startByte;
        headers['Range'] = `bytes=${startByte}-`;
        console.log(`[VideoDownloader] Resuming download from byte ${startByte}`);
      }

      // Start download
      const response = await axios({
        method: 'GET',
        url: videoUrl,
        headers,
        timeout: 30000,
        responseType: 'stream',
        maxRedirects: 5,
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.loaded) {
            progress.downloadedBytes = startByte + progressEvent.loaded;
          }
          if (progressEvent.total) {
            progress.totalBytes = startByte + progressEvent.total;
          }
        },
      });

      // Get total size
      const contentLength = response.headers['content-length'];
      if (contentLength) {
        progress.totalBytes = startByte + parseInt(contentLength, 10);
      }

      // Handle redirect to HLS playlist
      const finalUrl = response.request.res.responseUrl || videoUrl;
      if (finalUrl.includes('.m3u8') || response.headers['content-type']?.includes('application/vnd.apple.mpegurl')) {
        // For HLS, we need to use a different approach
        // For now, mark as failed with informative message
        throw new Error('HLS streams require special handling. Please use a download tool that supports HLS.');
      }

      // Write to file
      const writer = fs.createWriteStream(filePath, { flags: startByte > 0 ? 'a' : 'w' });
      
      await new Promise((resolve, reject) => {
        response.data.pipe(writer);
        
        writer.on('finish', () => {
          progress.status = DownloadStatus.COMPLETED;
          progress.endTime = Date.now();
          progress.percent = 100;
          this.emit('completed', progress.toJSON());
          resolve();
        });
        
        writer.on('error', (err) => {
          reject(err);
        });
        
        response.data.on('error', (err) => {
          reject(err);
        });
      });

    } catch (error) {
      console.error(`[VideoDownloader] Download error for ${episodeId}:`, error.message);
      progress.status = DownloadStatus.FAILED;
      progress.endTime = Date.now();
      progress.errorMessage = error.message;
      this.emit('error', progress.toJSON());
    } finally {
      // Process next item in queue
      this._processQueue();
    }
  }

  /**
   * Cancel a download
   */
  cancelDownload(episodeId) {
    const progress = this.activeDownloads.get(episodeId);
    if (!progress) {
      throw new Error('Download not found');
    }

    if (progress.status === DownloadStatus.DOWNLOADING) {
      progress.status = DownloadStatus.CANCELLED;
      progress.endTime = Date.now();
      this.emit('cancelled', progress.toJSON());
    }

    // Remove from queue if pending
    const queueIndex = this.downloadQueue.findIndex(item => item.episodeId === episodeId);
    if (queueIndex > -1) {
      this.downloadQueue.splice(queueIndex, 1);
    }

    return progress.toJSON();
  }

  /**
   * Get download progress
   */
  getProgress(episodeId) {
    const progress = this.progressMap.get(episodeId);
    return progress ? progress.toJSON() : null;
  }

  /**
   * Get all active downloads
   */
  getActiveDownloads() {
    return Array.from(this.activeDownloads.values())
      .filter(p => p.status === DownloadStatus.DOWNLOADING)
      .map(p => p.toJSON());
  }

  /**
   * Get all downloads (active + queued)
   */
  getAllDownloads() {
    const downloads = Array.from(this.progressMap.values()).map(p => p.toJSON());
    
    // Add queued items that don't have progress yet
    for (const item of this.downloadQueue) {
      if (!this.progressMap.has(item.episodeId)) {
        downloads.push({
          episodeId: item.episodeId,
          status: DownloadStatus.PENDING,
          animeTitle: item.anime.title,
          episodeNum: item.episode.episode || item.episode.title,
        });
      }
    }
    
    return downloads;
  }

  /**
   * Clear completed/failed downloads from memory
   */
  clearCompleted() {
    for (const [episodeId, progress] of this.progressMap) {
      if (progress.status === DownloadStatus.COMPLETED || 
          progress.status === DownloadStatus.FAILED ||
          progress.status === DownloadStatus.CANCELLED) {
        this.progressMap.delete(episodeId);
        this.activeDownloads.delete(episodeId);
      }
    }
  }

  /**
   * Destroy downloader
   */
  destroy() {
    this._stopProgressUpdates();
    this.removeAllListeners();
    this.downloadQueue = [];
    this.activeDownloads.clear();
    this.progressMap.clear();
  }
}

// Singleton instance
let videoDownloaderInstance = null;

export function getVideoDownloader(downloadDir, maxConcurrent = 2) {
  if (!videoDownloaderInstance) {
    videoDownloaderInstance = new VideoDownloader(downloadDir, maxConcurrent);
  }
  return videoDownloaderInstance;
}

export function resetVideoDownloader() {
  if (videoDownloaderInstance) {
    videoDownloaderInstance.destroy();
    videoDownloaderInstance = null;
  }
}

export default {
  VideoDownloader,
  DownloadProgress,
  DownloadStatus,
  getVideoDownloader,
  resetVideoDownloader,
};
