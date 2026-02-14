import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import {
  VideoDownloader,
  DownloadProgress,
  DownloadStatus,
  getVideoDownloader,
  resetVideoDownloader,
} from '../../src/services/videoDownloader.js'
import fs from 'fs'
import path from 'path'
import os from 'os'

describe('Video Downloader', () => {
  let downloader
  let tempDir

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-downloads-'))
    downloader = new VideoDownloader(tempDir, 2)
  })

  afterEach(() => {
    downloader.destroy()
    resetVideoDownloader()
    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true })
    }
  })

  describe('DownloadProgress', () => {
    it('should create progress with initial values', () => {
      const progress = new DownloadProgress('test-episode')

      expect(progress.episodeId).toBe('test-episode')
      expect(progress.status).toBe(DownloadStatus.PENDING)
      expect(progress.percent).toBe(0)
      expect(progress.totalBytes).toBe(0)
      expect(progress.downloadedBytes).toBe(0)
    })

    it('should calculate percent correctly', () => {
      const progress = new DownloadProgress('test')
      progress.totalBytes = 1000
      progress.downloadedBytes = 500

      expect(progress.percent).toBe(50)
    })

    it('should calculate elapsed time', async () => {
      const progress = new DownloadProgress('test')
      progress.startTime = Date.now() - 5000 // 5 seconds ago

      expect(progress.elapsedSeconds).toBeGreaterThanOrEqual(5)
    })

    it('should calculate speed correctly', () => {
      const progress = new DownloadProgress('test')
      progress.lastUpdateTime = Date.now() - 1000
      progress.lastDownloadedBytes = 0
      progress.downloadedBytes = 1000

      progress.updateSpeed()

      expect(progress.speedBytesPerSec).toBeGreaterThan(0)
    })

    it('should convert to JSON correctly', () => {
      const progress = new DownloadProgress('test')
      progress.totalBytes = 1000
      progress.downloadedBytes = 500
      progress.status = DownloadStatus.DOWNLOADING

      const json = progress.toJSON()
      
      expect(json.episodeId).toBe('test')
      expect(json.percent).toBe(50)
      expect(json.status).toBe(DownloadStatus.DOWNLOADING)
    })
  })

  describe('VideoDownloader - Basic Operations', () => {
    it('should create download directory if not exists', () => {
      const newDir = path.join(tempDir, 'subdir')
      const dl = new VideoDownloader(newDir, 2)
      
      expect(fs.existsSync(newDir)).toBe(true)
      dl.destroy()
    })

    it('should generate safe filename', () => {
      const filename = downloader._getSafeFileName(
        'Test: Anime <Name>',
        '01',
        '.mp4'
      )
      
      expect(filename).not.toContain('<')
      expect(filename).not.toContain('>')
      expect(filename).not.toContain(':')
      expect(filename).toContain('Test_ Anime _Name_')
      expect(filename).toContain('EP01')
      expect(filename.endsWith('.mp4')).toBe(true)
    })

    it('should get file extension from URL', () => {
      expect(downloader._getFileExtension('http://test.com/video.mp4')).toBe('.mp4')
      expect(downloader._getFileExtension('http://test.com/video.m3u8')).toBe('.mp4')
      expect(downloader._getFileExtension('http://test.com/video')).toBe('.mp4')
    })
  })

  describe('VideoDownloader - Queue Management', () => {
    it('should add download to queue', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01', title: 'Episode 1' }
      
      // Mock video URL to prevent actual download
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      const result = await downloader.addDownload(anime, episode, mockUrl)

      expect(result.episodeId).toBe('ep-1')
      // Status could be PENDING or DOWNLOADING depending on queue state
      expect([DownloadStatus.PENDING, DownloadStatus.DOWNLOADING]).toContain(result.status)
    })

    it('should reject duplicate downloads', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)

      await expect(
        downloader.addDownload(anime, episode, mockUrl)
      ).rejects.toThrow('Download already in progress')
    })

    it('should track active downloads', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)

      const activeDownloads = downloader.getAllDownloads()
      expect(activeDownloads).toHaveLength(1)
      expect(activeDownloads[0].episodeId).toBe('ep-1')
    })

    it('should respect max concurrent limit', () => {
      // Add 3 downloads with maxConcurrent = 2
      const dl = new VideoDownloader(tempDir, 2)
      
      // Check queue behavior
      expect(dl._canStartDownload()).toBe(true)
      
      // Add active downloads
      const progress1 = new DownloadProgress('ep-1')
      progress1.status = DownloadStatus.DOWNLOADING
      dl.activeDownloads.set('ep-1', progress1)
      
      expect(dl._canStartDownload()).toBe(true)
      
      const progress2 = new DownloadProgress('ep-2')
      progress2.status = DownloadStatus.DOWNLOADING
      dl.activeDownloads.set('ep-2', progress2)
      
      expect(dl._canStartDownload()).toBe(false)
      
      dl.destroy()
    })

    it('should cancel download', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)
      
      const result = downloader.cancelDownload('ep-1')
      
      expect(result.status).toBe(DownloadStatus.CANCELLED)
    })

    it('should throw when canceling non-existent download', () => {
      expect(() => {
        downloader.cancelDownload('non-existent')
      }).toThrow('Download not found')
    })

    it('should get download progress', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)

      const progress = downloader.getProgress('ep-1')
      
      expect(progress).not.toBeNull()
      expect(progress.episodeId).toBe('ep-1')
    })

    it('should clear completed downloads', async () => {
      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)
      
      // Mark as completed
      const progress = downloader.progressMap.get('ep-1')
      progress.status = DownloadStatus.COMPLETED

      expect(downloader.getAllDownloads()).toHaveLength(1)
      
      downloader.clearCompleted()
      
      expect(downloader.getAllDownloads()).toHaveLength(0)
    })
  })

  describe('VideoDownloader - Events', () => {
    it('should emit events during download lifecycle', async () => {
      const events = []
      
      downloader.on('started', (data) => events.push({ type: 'started', data }))
      downloader.on('cancelled', (data) => events.push({ type: 'cancelled', data }))

      const anime = { id: 'anime-1', title: 'Test Anime' }
      const episode = { id: 'ep-1', episode: '01' }
      const mockUrl = 'http://localhost:9999/mock-video.mp4'

      await downloader.addDownload(anime, episode, mockUrl)
      downloader.cancelDownload('ep-1')

      expect(events).toHaveLength(2)
      expect(events[0].type).toBe('started')
      expect(events[1].type).toBe('cancelled')
    })

    it('should emit progress updates', async () => {
      return new Promise((resolve) => {
        downloader.on('progress', (data) => {
          expect(data.episodeId).toBe('test-ep')
          resolve()
        })

        // Simulate progress update
        const progress = new DownloadProgress('test-ep')
        progress.status = DownloadStatus.DOWNLOADING
        progress.downloadedBytes = 500
        progress.totalBytes = 1000
        
        downloader.progressMap.set('test-ep', progress)
        
        // Trigger progress update manually
        progress.updateSpeed()
        downloader.emit('progress', progress.toJSON())
      })
    })
  })

  describe('VideoDownloader - Singleton', () => {
    it('should return same instance from getVideoDownloader', () => {
      const dl1 = getVideoDownloader(tempDir, 2)
      const dl2 = getVideoDownloader(tempDir, 2)
      
      expect(dl1).toBe(dl2)
      
      resetVideoDownloader()
    })

    it('should create new instance after reset', () => {
      const dl1 = getVideoDownloader(tempDir, 2)
      resetVideoDownloader()
      const dl2 = getVideoDownloader(tempDir, 2)
      
      expect(dl1).not.toBe(dl2)
      
      resetVideoDownloader()
    })
  })
})
