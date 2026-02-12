/**
 * 下载服务
 * 
 * 对应原项目: src/services/video_downloader.py
 * 职责: 视频下载任务管理
 */

import type { DatabaseService } from '../database'
import type { DownloadTask, AutoDownloadConfig } from '@shared/types'

export class DownloadService {
  private databaseService: DatabaseService
  private tasks: Map<string, DownloadTask> = new Map()

  constructor(databaseService: DatabaseService) {
    this.databaseService = databaseService
  }

  async getTasks(): Promise<DownloadTask[]> {
    return Array.from(this.tasks.values())
  }

  async addTask(url: string, filename: string): Promise<DownloadTask> {
    // TODO: 实现下载任务添加
    const task: DownloadTask = {
      id: Date.now().toString(),
      animeId: '',
      episodeId: '',
      title: '',
      episodeTitle: filename,
      url,
      status: 'pending',
      progress: 0,
      speed: 0,
      totalSize: 0,
      downloadedSize: 0,
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    
    this.tasks.set(task.id, task)
    return task
  }

  async pauseTask(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId)
    if (task) {
      task.status = 'paused'
    }
  }

  async resumeTask(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId)
    if (task) {
      task.status = 'downloading'
    }
  }

  async cancelTask(taskId: string): Promise<void> {
    this.tasks.delete(taskId)
  }

  async pauseAll(): Promise<void> {
    for (const task of this.tasks.values()) {
      if (task.status === 'downloading') {
        task.status = 'paused'
      }
    }
  }
}
