/**
 * 数据库服务
 * 
 * 对应原项目: src/models/database.py
 * 技术栈: better-sqlite3 (替代 Peewee)
 */

import Database from 'better-sqlite3'
import { app } from 'electron'
import { join } from 'path'
import { mkdirSync } from 'fs'
import log from 'electron-log'
import type { FavoriteAnime, PlaybackHistory } from '@shared/types'

// 数据库文件路径
const DB_FILE_NAME = 'anime1.db'

export class DatabaseService {
  private db: Database.Database | null = null
  private dbPath: string

  constructor() {
    const userDataPath = app.getPath('userData')
    this.dbPath = join(userDataPath, DB_FILE_NAME)
    
    // 确保目录存在
    mkdirSync(userDataPath, { recursive: true })
  }

  /**
   * 连接数据库
   */
  async connect(): Promise<void> {
    try {
      this.db = new Database(this.dbPath)
      
      // 启用 WAL 模式，提高并发性能
      this.db.pragma('journal_mode = WAL')
      this.db.pragma('foreign_keys = ON')
      
      // 初始化表
      this.initTables()
      
      // 运行迁移
      this.runMigrations()
      
      log.info(`[Database] Connected to ${this.dbPath}`)
    } catch (error) {
      log.error('[Database] Failed to connect:', error)
      throw error
    }
  }

  /**
   * 关闭数据库
   */
  close(): void {
    if (this.db) {
      this.db.close()
      this.db = null
      log.info('[Database] Connection closed')
    }
  }

  /**
   * 初始化数据表
   */
  private initTables(): void {
    if (!this.db) return

    // 收藏表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS favorite_anime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        cover_url TEXT,
        detail_url TEXT NOT NULL,
        created_at INTEGER NOT NULL
      )
    `)

    // 封面缓存表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS cover_cache (
        anime_id TEXT PRIMARY KEY,
        cover_url TEXT,
        year TEXT,
        season TEXT,
        subtitle_group TEXT,
        bangumi_info TEXT,
        cached_at INTEGER NOT NULL
      )
    `)

    // 播放历史表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS playback_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id TEXT NOT NULL,
        episode_id TEXT NOT NULL,
        title TEXT NOT NULL,
        episode_title TEXT NOT NULL,
        progress INTEGER DEFAULT 0,
        duration INTEGER DEFAULT 0,
        played_at INTEGER NOT NULL
      )
    `)

    // 设置表
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    `)

    // 创建索引
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_favorite_anime_id ON favorite_anime(anime_id);
      CREATE INDEX IF NOT EXISTS idx_cover_cache_anime_id ON cover_cache(anime_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_anime_id ON playback_history(anime_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_played_at ON playback_history(played_at);
    `)
  }

  /**
   * 运行数据库迁移
   */
  private runMigrations(): void {
    // 迁移记录表
    this.db?.exec(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at INTEGER NOT NULL
      )
    `)

    // 获取当前版本
    const result = this.db?.prepare('SELECT MAX(version) as version FROM schema_migrations').get() as { version: number | null }
    const currentVersion = result?.version ?? 0

    // 定义迁移
    const migrations = [
      {
        version: 1,
        description: 'Initial schema',
        up: () => {
          // 初始表已在 initTables 中创建
        }
      }
      // 后续迁移在这里添加
    ]

    // 执行待执行的迁移
    for (const migration of migrations) {
      if (migration.version > currentVersion) {
        log.info(`[Database] Running migration ${migration.version}: ${migration.description}`)
        migration.up()
        this.db?.prepare('INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)').run(migration.version, Date.now())
      }
    }
  }

  // ==========================================
  // 收藏相关操作
  // ==========================================

  getFavorites(): FavoriteAnime[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM favorite_anime ORDER BY created_at DESC')
    const rows = stmt.all() as any[]
    
    return rows.map(row => ({
      id: row.id,
      animeId: row.anime_id,
      title: row.title,
      coverUrl: row.cover_url,
      detailUrl: row.detail_url,
      createdAt: row.created_at
    }))
  }

  addFavorite(favorite: Omit<FavoriteAnime, 'id' | 'createdAt'>): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO favorite_anime (anime_id, title, cover_url, detail_url, created_at)
      VALUES (?, ?, ?, ?, ?)
    `)
    
    stmt.run(
      favorite.animeId,
      favorite.title,
      favorite.coverUrl,
      favorite.detailUrl,
      Date.now()
    )
  }

  removeFavorite(animeId: string): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('DELETE FROM favorite_anime WHERE anime_id = ?')
    stmt.run(animeId)
  }

  isFavorite(animeId: string): boolean {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT COUNT(*) as count FROM favorite_anime WHERE anime_id = ?')
    const result = stmt.get(animeId) as { count: number }
    
    return result.count > 0
  }

  // ==========================================
  // 封面缓存相关操作
  // ==========================================

  getCoverCache(animeId: string): Record<string, any> | null {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM cover_cache WHERE anime_id = ?')
    const row = stmt.get(animeId) as any
    
    if (!row) return null
    
    return {
      animeId: row.anime_id,
      coverUrl: row.cover_url,
      year: row.year,
      season: row.season,
      subtitleGroup: row.subtitle_group,
      bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : null,
      cachedAt: row.cached_at
    }
  }

  setCoverCache(animeId: string, data: Record<string, any>): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO cover_cache 
      (anime_id, cover_url, year, season, subtitle_group, bangumi_info, cached_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `)
    
    stmt.run(
      animeId,
      data.coverUrl,
      data.year,
      data.season,
      data.subtitleGroup,
      data.bangumiInfo ? JSON.stringify(data.bangumiInfo) : null,
      Date.now()
    )
  }

  // ==========================================
  // 播放历史相关操作
  // ==========================================

  getPlaybackHistory(): PlaybackHistory[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM playback_history ORDER BY played_at DESC LIMIT 100')
    const rows = stmt.all() as any[]
    
    return rows.map(row => ({
      id: row.id,
      animeId: row.anime_id,
      episodeId: row.episode_id,
      title: row.title,
      episodeTitle: row.episode_title,
      progress: row.progress,
      duration: row.duration,
      playedAt: row.played_at
    }))
  }

  addPlaybackHistory(history: Omit<PlaybackHistory, 'id'>): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      INSERT INTO playback_history 
      (anime_id, episode_id, title, episode_title, progress, duration, played_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `)
    
    stmt.run(
      history.animeId,
      history.episodeId,
      history.title,
      history.episodeTitle,
      history.progress,
      history.duration,
      Date.now()
    )
  }

  clearPlaybackHistory(): void {
    if (!this.db) throw new Error('Database not connected')
    
    this.db.exec('DELETE FROM playback_history')
  }

  // ==========================================
  // 设置相关操作
  // ==========================================

  getSetting(key: string): string | null {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT value FROM settings WHERE key = ?')
    const row = stmt.get(key) as { value: string } | undefined
    
    return row?.value ?? null
  }

  setSetting(key: string, value: string): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)')
    stmt.run(key, value)
  }

  getAllSettings(): Record<string, string> {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT key, value FROM settings')
    const rows = stmt.all() as Array<{ key: string; value: string }>
    
    const settings: Record<string, string> = {}
    for (const row of rows) {
      settings[row.key] = row.value
    }
    
    return settings
  }
}
