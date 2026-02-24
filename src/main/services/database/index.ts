/**
 * 数据库服务
 * 
 * 对应原项目: src/models/database.py, src/models/cover_cache.py
 * 技术栈: better-sqlite3 (替代 Peewee)
 */

import type { Database as DatabaseType } from 'libsql'
import { app } from 'electron'
import { join } from 'path'
import { mkdirSync } from 'fs'
import log from 'electron-log'
import type { FavoriteAnime, PlaybackHistory, BangumiInfo, CoverCache } from '@shared/types'
import { migrateData, needsMigration, isMigrationCompleted, markMigrationCompleted } from './migrate'

// 数据库文件路径
const DB_FILE_NAME = 'anime1.db'

// 动态导入 libsql 避免打包问题
let Database: typeof DatabaseType.Database

export class DatabaseService {
  private db: DatabaseType | null = null
  private dbPath: string

  constructor() {
    const userDataPath = app.getPath('userData')
    this.dbPath = join(userDataPath, DB_FILE_NAME)
    
    // 确保目录存在
    mkdirSync(userDataPath, { recursive: true })
  }

  private async loadDatabase(): Promise<typeof DatabaseType> {
    if (!Database) {
      // libsql 默认导出 Database 类
      Database = await import('libsql').then(m => m.default || m)
    }
    return Database
  }

  /**
   * 连接数据库
   */
  async connect(): Promise<void> {
    try {
      const DatabaseClass = await this.loadDatabase()
      this.db = new DatabaseClass(this.dbPath)
      
      // 启用 WAL 模式，提高并发性能
      this.db.pragma('journal_mode = WAL')
      this.db.pragma('foreign_keys = ON')
      
      // 初始化表
      this.initTables()
      
      // 运行迁移
      this.runMigrations()
      
      // 数据迁移（从旧版本）
      if (needsMigration() && !isMigrationCompleted()) {
        log.info('[Database] Legacy database detected, starting migration...')
        const result = await migrateData(this)
        if (result.success) {
          markMigrationCompleted()
          log.info('[Database] Migration completed:', result.message)
          if (result.stats) {
            log.info('[Database] Migration stats:', result.stats)
          }
        } else {
          log.error('[Database] Migration failed:', result.message)
        }
      }
      
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
   * 获取数据库实例
   */
  getDatabase(): Database.Database {
    if (!this.db) {
      throw new Error('Database not connected')
    }
    return this.db
  }

  /**
   * 初始化数据表
   */
  private initTables(): void {
    if (!this.db) return

    // 收藏表 - 对应原 FavoriteAnime Model
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS favorite_anime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        detail_url TEXT NOT NULL,
        episode INTEGER DEFAULT 0,
        cover_url TEXT,
        year TEXT,
        season TEXT,
        subtitle_group TEXT,
        last_episode INTEGER DEFAULT 0,
        added_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )
    `)

    // 封面缓存表 - 对应原 CoverCache Model
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS cover_cache (
        anime_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        year TEXT,
        season TEXT,
        cover_url TEXT,
        episode INTEGER DEFAULT 0,
        cover_data TEXT NOT NULL,
        bangumi_info TEXT,
        cached_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )
    `)

    // 播放历史表 - 对应原 PlaybackHistory Model
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS playback_history (
        id TEXT PRIMARY KEY,
        anime_id TEXT NOT NULL,
        anime_title TEXT NOT NULL,
        episode_id TEXT NOT NULL,
        episode_num INTEGER NOT NULL,
        position_seconds REAL DEFAULT 0,
        total_seconds REAL DEFAULT 0,
        last_watched_at INTEGER NOT NULL,
        cover_url TEXT
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
      CREATE INDEX IF NOT EXISTS idx_cover_cache_year ON cover_cache(year);
      CREATE INDEX IF NOT EXISTS idx_cover_cache_season ON cover_cache(season);
      CREATE INDEX IF NOT EXISTS idx_cover_cache_cached_at ON cover_cache(cached_at);
      CREATE INDEX IF NOT EXISTS idx_playback_history_anime_id ON playback_history(anime_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_episode_id ON playback_history(episode_id);
      CREATE INDEX IF NOT EXISTS idx_playback_history_last_watched ON playback_history(last_watched_at);
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

  /**
   * 获取所有收藏
   */
  getFavorites(): FavoriteAnime[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      SELECT * FROM favorite_anime ORDER BY added_at DESC
    `)
    const rows = stmt.all() as any[]
    
    return rows.map(row => ({
      dbId: row.id,
      animeId: row.anime_id,
      title: row.title,
      detailUrl: row.detail_url,
      episode: row.episode,
      coverUrl: row.cover_url,
      year: row.year,
      season: row.season,
      subtitleGroup: row.subtitle_group,
      lastEpisode: row.last_episode,
      addedAt: row.added_at,
      updatedAt: row.updated_at
    }))
  }

  /**
   * 添加收藏
   */
  addFavorite(favorite: Omit<FavoriteAnime, 'dbId' | 'addedAt' | 'updatedAt'>): void {
    if (!this.db) throw new Error('Database not connected')
    
    const now = Date.now()
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO favorite_anime 
      (anime_id, title, detail_url, episode, cover_url, year, season, subtitle_group, last_episode, added_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT added_at FROM favorite_anime WHERE anime_id = ?), ?), ?)
    `)
    
    stmt.run(
      favorite.animeId,
      favorite.title,
      favorite.detailUrl,
      favorite.episode ?? 0,
      favorite.coverUrl ?? null,
      favorite.year ?? null,
      favorite.season ?? null,
      favorite.subtitleGroup ?? null,
      favorite.lastEpisode ?? 0,
      favorite.animeId, // 用于 COALESCE 查询原 added_at
      now,
      now
    )
  }

  /**
   * 移除收藏
   */
  removeFavorite(animeId: string): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('DELETE FROM favorite_anime WHERE anime_id = ?')
    stmt.run(animeId)
  }

  /**
   * 检查是否已收藏
   */
  isFavorite(animeId: string): boolean {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT COUNT(*) as count FROM favorite_anime WHERE anime_id = ?')
    const result = stmt.get(animeId) as { count: number }
    
    return result.count > 0
  }

  /**
   * 更新收藏的最新集数
   */
  updateFavoriteLastEpisode(animeId: string, lastEpisode: number): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      UPDATE favorite_anime 
      SET last_episode = ?, updated_at = ?
      WHERE anime_id = ?
    `)
    stmt.run(lastEpisode, Date.now(), animeId)
  }

  // ==========================================
  // 封面缓存相关操作 (CoverCache Model)
  // ==========================================

  /**
   * 获取封面缓存
   */
  getCoverCache(animeId: string): CoverCache | null {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM cover_cache WHERE anime_id = ?')
    const row = stmt.get(animeId) as any
    
    if (!row) return null
    
    return {
      animeId: row.anime_id,
      title: row.title,
      year: row.year,
      season: row.season,
      coverUrl: row.cover_url,
      episode: row.episode,
      coverData: JSON.parse(row.cover_data),
      bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined,
      cachedAt: row.cached_at,
      updatedAt: row.updated_at
    }
  }

  /**
   * 批量获取封面缓存
   */
  getCoverCaches(animeIds: string[]): Record<string, CoverCache> {
    if (!this.db) throw new Error('Database not connected')
    if (animeIds.length === 0) return {}
    
    const placeholders = animeIds.map(() => '?').join(',')
    const stmt = this.db.prepare(`
      SELECT * FROM cover_cache WHERE anime_id IN (${placeholders})
    `)
    const rows = stmt.all(...animeIds) as any[]
    
    const result: Record<string, CoverCache> = {}
    for (const row of rows) {
      result[row.anime_id] = {
        animeId: row.anime_id,
        title: row.title,
        year: row.year,
        season: row.season,
        coverUrl: row.cover_url,
        episode: row.episode,
        coverData: JSON.parse(row.cover_data),
        bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined,
        cachedAt: row.cached_at,
        updatedAt: row.updated_at
      }
    }
    
    return result
  }

  /**
   * 设置封面缓存
   */
  setCoverCache(animeId: string, coverData: Record<string, any>, bangumiInfo?: BangumiInfo): void {
    if (!this.db) throw new Error('Database not connected')
    
    const now = Date.now()
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO cover_cache 
      (anime_id, title, year, season, cover_url, episode, cover_data, bangumi_info, cached_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
    
    stmt.run(
      animeId,
      coverData.title ?? '',
      coverData.year ?? null,
      coverData.season ?? null,
      coverData.cover_url ?? null,
      coverData.episode ?? 0,
      JSON.stringify(coverData),
      bangumiInfo ? JSON.stringify(bangumiInfo) : null,
      now,
      now
    )
  }

  /**
   * 批量设置封面缓存
   */
  setCoverCaches(covers: Record<string, Record<string, any>>, bangumiInfos?: Record<string, BangumiInfo>): number {
    if (!this.db) throw new Error('Database not connected')
    
    const now = Date.now()
    const insert = this.db.prepare(`
      INSERT OR REPLACE INTO cover_cache 
      (anime_id, title, year, season, cover_url, episode, cover_data, bangumi_info, cached_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
    
    let count = 0
    const insertMany = this.db.transaction((items: [string, Record<string, any>][]) => {
      for (const [animeId, coverData] of items) {
        const bangumiInfo = bangumiInfos?.[animeId]
        insert.run(
          animeId,
          coverData.title ?? '',
          coverData.year ?? null,
          coverData.season ?? null,
          coverData.cover_url ?? null,
          coverData.episode ?? 0,
          JSON.stringify(coverData),
          bangumiInfo ? JSON.stringify(bangumiInfo) : null,
          now,
          now
        )
        count++
      }
    })
    
    insertMany(Object.entries(covers))
    return count
  }

  /**
   * 更新 Bangumi 信息
   */
  setBangumiInfo(animeId: string, bangumiInfo: BangumiInfo): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      UPDATE cover_cache 
      SET bangumi_info = ?, updated_at = ?
      WHERE anime_id = ?
    `)
    stmt.run(JSON.stringify(bangumiInfo), Date.now(), animeId)
  }

  /**
   * 获取 Bangumi 信息
   */
  getBangumiInfo(animeId: string): BangumiInfo | null {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT bangumi_info FROM cover_cache WHERE anime_id = ?')
    const row = stmt.get(animeId) as { bangumi_info: string } | undefined
    
    if (!row?.bangumi_info) return null
    
    try {
      return JSON.parse(row.bangumi_info)
    } catch {
      return null
    }
  }

  /**
   * 按年份获取缓存
   */
  getCoverCachesByYear(year: string): CoverCache[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM cover_cache WHERE year = ?')
    const rows = stmt.all(year) as any[]
    
    return rows.map(row => ({
      animeId: row.anime_id,
      title: row.title,
      year: row.year,
      season: row.season,
      coverUrl: row.cover_url,
      episode: row.episode,
      coverData: JSON.parse(row.cover_data),
      bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined,
      cachedAt: row.cached_at,
      updatedAt: row.updated_at
    }))
  }

  /**
   * 按季节获取缓存
   */
  getCoverCachesBySeason(season: string): CoverCache[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM cover_cache WHERE season = ?')
    const rows = stmt.all(season) as any[]
    
    return rows.map(row => ({
      animeId: row.anime_id,
      title: row.title,
      year: row.year,
      season: row.season,
      coverUrl: row.cover_url,
      episode: row.episode,
      coverData: JSON.parse(row.cover_data),
      bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined,
      cachedAt: row.cached_at,
      updatedAt: row.updated_at
    }))
  }

  /**
   * 搜索标题
   */
  searchCoverCachesByTitle(keyword: string): CoverCache[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT * FROM cover_cache WHERE title LIKE ?')
    const rows = stmt.all(`%${keyword}%`) as any[]
    
    return rows.map(row => ({
      animeId: row.anime_id,
      title: row.title,
      year: row.year,
      season: row.season,
      coverUrl: row.cover_url,
      episode: row.episode,
      coverData: JSON.parse(row.cover_data),
      bangumiInfo: row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined,
      cachedAt: row.cached_at,
      updatedAt: row.updated_at
    }))
  }

  /**
   * 获取所有缓存的 anime_id
   */
  getAllCachedIds(): Set<string> {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT anime_id FROM cover_cache')
    const rows = stmt.all() as Array<{ anime_id: string }>
    
    return new Set(rows.map(r => r.anime_id))
  }

  /**
   * 获取缓存数量
   */
  getCoverCacheCount(): number {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT COUNT(*) as count FROM cover_cache')
    const result = stmt.get() as { count: number }
    return result.count
  }

  /**
   * 清空所有缓存
   */
  clearCoverCaches(): void {
    if (!this.db) throw new Error('Database not connected')
    this.db.exec('DELETE FROM cover_cache')
  }

  // ==========================================
  // 播放历史相关操作 (PlaybackHistory Model)
  // ==========================================

  /**
   * 获取播放历史
   */
  getPlaybackHistory(limit: number = 100): PlaybackHistory[] {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare(`
      SELECT * FROM playback_history 
      ORDER BY last_watched_at DESC 
      LIMIT ?
    `)
    const rows = stmt.all(limit) as any[]
    
    return rows.map(row => ({
      id: row.id,
      animeId: row.anime_id,
      animeTitle: row.anime_title,
      episodeId: row.episode_id,
      episodeNum: row.episode_num,
      positionSeconds: row.position_seconds,
      totalSeconds: row.total_seconds,
      lastWatchedAt: row.last_watched_at,
      coverUrl: row.cover_url
    }))
  }

  /**
   * 添加/更新播放历史
   */
  addPlaybackHistory(history: Omit<PlaybackHistory, 'id'>): void {
    if (!this.db) throw new Error('Database not connected')
    
    const id = `${history.animeId}_${history.episodeId}`
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO playback_history 
      (id, anime_id, anime_title, episode_id, episode_num, position_seconds, total_seconds, last_watched_at, cover_url)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `)
    
    stmt.run(
      id,
      history.animeId,
      history.animeTitle,
      history.episodeId,
      history.episodeNum,
      history.positionSeconds,
      history.totalSeconds,
      history.lastWatchedAt,
      history.coverUrl ?? null
    )
  }

  /**
   * 获取特定剧集的播放进度
   */
  getPlaybackProgress(animeId: string, episodeId: string): { position: number; total: number } | null {
    if (!this.db) throw new Error('Database not connected')
    
    const id = `${animeId}_${episodeId}`
    const stmt = this.db.prepare(`
      SELECT position_seconds, total_seconds FROM playback_history WHERE id = ?
    `)
    const row = stmt.get(id) as { position_seconds: number; total_seconds: number } | undefined
    
    if (!row) return null
    
    return {
      position: row.position_seconds,
      total: row.total_seconds
    }
  }

  /**
   * 清除播放历史
   */
  clearPlaybackHistory(): void {
    if (!this.db) throw new Error('Database not connected')
    this.db.exec('DELETE FROM playback_history')
  }

  // ==========================================
  // 设置相关操作
  // ==========================================

  /**
   * 获取设置
   */
  getSetting(key: string): string | null {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('SELECT value FROM settings WHERE key = ?')
    const row = stmt.get(key) as { value: string } | undefined
    
    return row?.value ?? null
  }

  /**
   * 设置值
   */
  setSetting(key: string, value: string): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)')
    stmt.run(key, value)
  }

  /**
   * 获取所有设置
   */
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

  /**
   * 删除设置
   */
  deleteSetting(key: string): void {
    if (!this.db) throw new Error('Database not connected')
    
    const stmt = this.db.prepare('DELETE FROM settings WHERE key = ?')
    stmt.run(key)
  }
}
