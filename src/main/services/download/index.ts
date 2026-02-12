/**
 * 下载服务
 * 
 * 对应原项目: src/services/video_downloader.py
 * 职责: 视频下载任务管理
 */

import { EventEmitter } from 'events'
import { join } from 'path'
import { createWriteStream, existsSync, mkdirSync, statSync } from 'fs'
import axios from 'axios'
import log from 'electron-log'
import type { DatabaseService } from '../database'
import type { DownloadTask, CreateDownloadTaskParams } from '@shared/types'
import { DOWNLOAD_CONFIG } from '@shared/constants'
import { PATHS } from '../../config'

export class DownloadService extends EventEmitter {
  private databaseService: DatabaseService
  private tasks: Map<string, DownloadTask> = new Map()
  private activeDownloads: Map<string, AbortController> = new Map()

  constructor(databaseService: DatabaseService) {
    super()
    this.databaseService = databaseService
  }

  /**
   * 获取所有任务
   */
  getTasks(): DownloadTask[] {
    return Array.from(this.tasks.values()).sort((a, b) => b.createdAt - a.createdAt)
  }

  /**
   * 获取单个任务
   */
  getTask(taskId: string): DownloadTask | undefined {
    return this.tasks.get(taskId)
  }

  /**
   * 添加下载任务
   */
  async addTask(params: CreateDownloadTaskParams): Promise<DownloadTask> {
    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // 确保下载目录存在
    const downloadPath = PATHS.DEFAULT_DOWNLOAD_DIR
    if (!existsSync(downloadPath)) {
      mkdirSync(downloadPath, { recursive: true })
    }
    
    const task: DownloadTask = {
      id: taskId,
      animeId: params.animeId || '',
      episodeId: params.episodeId || '',
      title: params.title || params.filename,
      episodeTitle: params.episodeTitle || params.filename,
      url: params.url,
      status: 'pending',
      progress: 0,
      speed: 0,
      totalSize: 0,
      downloadedSize: 0,
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    
    this.tasks.set(taskId, task)
    this.emit('taskAdded', task)
    
    // 自动开始下载
    this.startDownload(task)
    
    return task
  }

  /**
   * 开始下载
   */
  private async startDownload(task: DownloadTask): Promise<void> {
    if (task.status === 'downloading' || task.status === 'completed') {
      return
    }
    
    // 检查是否超过最大并发数
    const activeCount = Array.from(this.tasks.values()).filter(
      t => t.status === 'downloading'
    ).length
    
    if (activeCount >= DOWNLOAD_CONFIG.MAX_CONCURRENT) {
      task.status = 'pending'
      this.updateTask(task)
      return
    }
    
    task.status = 'downloading'
    this.updateTask(task)
    
    const abortController = new AbortController()
    this.activeDownloads.set(task.id, abortController)
    
    try {
      const filePath = join(PATHS.DEFAULT_DOWNLOAD_DIR, `${task.episodeTitle}.mp4`)
      
      // 检查是否支持断点续传
      let startByte = 0
      if (existsSync(filePath)) {
        const stats = statSync(filePath)
        startByte = stats.size
        task.downloadedSize = startByte
      }
      
      // 发起请求
      const response = await axios({
        method: 'get',
        url: task.url,
        responseType: 'stream',
        signal: abortController.signal,
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          ...(startByte > 0 && { Range: `bytes=${startByte}-` })
        },
        timeout: DOWNLOAD_CONFIG.TIMEOUT
      })
      
      // 获取总大小
      const contentLength = response.headers['content-length']
      if (contentLength) {
        task.totalSize = parseInt(contentLength, 10) + startByte
      }
      
      // 创建写入流
      const writer = createWriteStream(filePath, { flags: startByte > 0 ? 'a' : 'w' })
      
      // 下载进度跟踪
      let lastUpdate = Date.now()
      let lastDownloaded = task.downloadedSize
      
      response.data.on('data', (chunk: Buffer) => {
        task.downloadedSize += chunk.length
        
        // 计算速度（每秒更新）
        const now = Date.now()
        if (now - lastUpdate >= 1000) {
          const timeDiff = (now - lastUpdate) / 1000
          const byteDiff = task.downloadedSize - lastDownloaded
          task.speed = Math.floor(byteDiff / timeDiff)
          
          // 计算进度
          if (task.totalSize > 0) {
            task.progress = Math.floor((task.downloadedSize / task.totalSize) * 100)
          }
          
          this.updateTask(task)
          this.emit('progress', task)
          
          lastUpdate = now
          lastDownloaded = task.downloadedSize
        }
      })
      
      // 等待下载完成
      await new Promise<void>((resolve, reject) => {
        response.data.pipe(writer)
        
        writer.on('finish', () => {
          task.status = 'completed'
          task.progress = 100
          task.speed = 0
          this.updateTask(task)
          this.emit('completed', task)
          resolve()
        })
        
        writer.on('error', (error) => {
          task.status = 'error'
          task.errorMessage = error.message
          this.updateTask(task)
          this.emit('error', task, error)
          reject(error)
        })
        
        response.data.on('error', (error: Error) => {
          writer.destroy()
          task.status = 'error'
          task.errorMessage = error.message
          this.updateTask(task)
          this.emit('error', task, error)
          reject(error)
        })
      })
      
    } catch (error: any) {
      if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
        task.status = 'paused'
        task.errorMessage = 'Download paused'
      } else {
        task.status = 'error'
        task.errorMessage = error.message
        this.emit('error', task, error)
      }
      
      this.updateTask(task)
    } finally {
      this.activeDownloads.delete(task.id)
      
      // 处理队列中的下一个任务
      this.processQueue()
    }
  }

  /**
   * 处理下载队列
   */
  private processQueue(): void {
    const pendingTask = Array.from(this.tasks.values()).find(
      t => t.status === 'pending'
    )
    
    if (pendingTask) {
      this.startDownload(pendingTask)
    }
  }

  /**
   * 暂停任务
   */
  pauseTask(taskId: string): void {
    const task = this.tasks.get(taskId)
    if (!task) return
    
    const controller = this.activeDownloads.get(taskId)
    if (controller) {
      controller.abort()
      this.activeDownloads.delete(taskId)
    }
    
    if (task.status === 'downloading') {
      task.status = 'paused'
      task.speed = 0
      this.updateTask(task)
    }
  }

  /**
   * 恢复任务
   */
  resumeTask(taskId: string): void {
    const task = this.tasks.get(taskId)
    if (!task || task.status !== 'paused') return
    
    task.status = 'pending'
    this.updateTask(task)
    
    this.processQueue()
  }

  /**
   * 取消任务
   */
  cancelTask(taskId: string): void {
    const task = this.tasks.get(taskId)
    if (!task) return
    
    const controller = this.activeDownloads.get(taskId)
    if (controller) {
      controller.abort()
      this.activeDownloads.delete(taskId)
    }
    
    task.status = 'error'
    task.errorMessage = 'Download cancelled'
    task.speed = 0
    this.updateTask(task)
  }

  /**
   * 删除任务
   */
  removeTask(taskId: string): void {
    this.cancelTask(taskId)
    this.tasks.delete(taskId)
    this.emit('taskRemoved', taskId)
  }

  /**
   * 暂停所有任务
   */
  async pauseAll(): Promise<void> {
    for (const [taskId, task] of this.tasks) {
      if (task.status === 'downloading') {
        this.pauseTask(taskId)
      }
    }
  }

  /**
   * 更新任务
   */
  private updateTask(task: DownloadTask): void {
    task.updatedAt = Date.now()
    this.emit('taskUpdated', task)
  }
}
