/**
 * 数据迁移脚本
 * 
 * 从原项目 Python 版本迁移数据到 Electron 版本
 * 原数据库: ~/Library/Application Support/Anime1/anime1.db (macOS)
 *          %APPDATA%/Anime1/anime1.db (Windows)
 */

import { app } from 'electron'
import { join, dirname } from 'path'
import { existsSync, copyFileSync } from 'fs'
import type { Database as DatabaseType } from 'libsql'
import log from 'electron-log'
import type { DatabaseService } from './index'

// 动态导入 libsql
async function loadDatabase(): Promise<typeof DatabaseType> {
  // libsql 默认导出 Database 类
  return await import('libsql').then(m => m.default || m)
}

/**
 * 获取原项目数据库路径
 */
function getLegacyDbPath(): string | null {
  const home = app.getPath('home')
  
  // macOS
  if (process.platform === 'darwin') {
    const macPath = join(home, 'Library', 'Application Support', 'Anime1', 'anime1.db')
    if (existsSync(macPath)) return macPath
  }
  
  // Windows
  if (process.platform === 'win32') {
    const appData = process.env.APPDATA
    if (appData) {
      const winPath = join(appData, 'Anime1', 'anime1.db')
      if (existsSync(winPath)) return winPath
    }
  }
  
  // Linux
  const linuxPath = join(home, '.local', 'share', 'Anime1', 'anime1.db')
  if (existsSync(linuxPath)) return linuxPath
  
  return null
}

/**
 * 检查是否需要迁移
 */
export function needsMigration(): boolean {
  const legacyPath = getLegacyDbPath()
  if (!legacyPath) return false
  
  const newDbPath = join(app.getPath('userData'), 'anime1.db')
  
  // 如果新数据库已存在，不需要迁移
  if (existsSync(newDbPath)) return false
  
  return true
}

/**
 * 迁移数据
 */
export async function migrateData(databaseService: DatabaseService): Promise<{ success: boolean; message: string; stats?: MigrationStats }> {
  const legacyPath = getLegacyDbPath()
  
  if (!legacyPath) {
    return { success: true, message: 'No legacy database found, fresh install' }
  }
  
  const newDbPath = join(app.getPath('userData'), 'anime1.db')
  
  // 如果新数据库已存在，跳过迁移
  if (existsSync(newDbPath)) {
    return { success: true, message: 'New database already exists, skipping migration' }
  }
  
  log.info(`[Migration] Found legacy database at: ${legacyPath}`)
  
  try {
    // 连接旧数据库
    const Database = await loadDatabase()
    const legacyDb = new Database(legacyPath, { readonly: true })
    
    const stats: MigrationStats = {
      favorites: 0,
      coverCaches: 0,
      playbackHistory: 0,
      settings: 0
    }
    
    // 迁移收藏
    stats.favorites = await migrateFavorites(legacyDb, databaseService)
    
    // 迁移封面缓存
    stats.coverCaches = await migrateCoverCaches(legacyDb, databaseService)
    
    // 迁移播放历史
    stats.playbackHistory = await migratePlaybackHistory(legacyDb, databaseService)
    
    // 迁移设置
    stats.settings = await migrateSettings(legacyDb, databaseService)
    
    legacyDb.close()
    
    log.info('[Migration] Migration completed successfully', stats)
    
    return {
      success: true,
      message: 'Migration completed successfully',
      stats
    }
  } catch (error) {
    log.error('[Migration] Migration failed:', error)
    return {
      success: false,
      message: `Migration failed: ${error}`
    }
  }
}

/**
 * 迁移统计
 */
interface MigrationStats {
  favorites: number
  coverCaches: number
  playbackHistory: number
  settings: number
}

/**
 * 迁移收藏数据
 */
async function migrateFavorites(legacyDb: Database.Database, newDb: DatabaseService): Promise<number> {
  try {
    // 检查旧表是否存在
    const tableExists = legacyDb.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' AND name='favoriteanime'
    `).get()
    
    if (!tableExists) {
      log.info('[Migration] No favoriteanime table in legacy database')
      return 0
    }
    
    const rows = legacyDb.prepare('SELECT * FROM favoriteanime').all() as any[]
    
    for (const row of rows) {
      newDb.addFavorite({
        animeId: row.id,
        title: row.title,
        detailUrl: row.detail_url,
        episode: row.episode ?? 0,
        coverUrl: row.cover_url,
        year: row.year,
        season: row.season,
        subtitleGroup: row.subtitle_group,
        lastEpisode: row.last_episode ?? 0
      })
    }
    
    log.info(`[Migration] Migrated ${rows.length} favorites`)
    return rows.length
  } catch (error) {
    log.error('[Migration] Failed to migrate favorites:', error)
    return 0
  }
}

/**
 * 迁移封面缓存数据
 */
async function migrateCoverCaches(legacyDb: Database.Database, newDb: DatabaseService): Promise<number> {
  try {
    // 检查旧表是否存在 (可能是 covercache 或 cover_cache)
    const tableInfo = legacyDb.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' AND (name='covercache' OR name='cover_cache')
    `).get() as { name: string } | undefined
    
    if (!tableInfo) {
      log.info('[Migration] No covercache table in legacy database')
      return 0
    }
    
    const tableName = tableInfo.name
    const rows = legacyDb.prepare(`SELECT * FROM ${tableName}`).all() as any[]
    
    for (const row of rows) {
      let coverData: Record<string, any>
      let bangumiInfo: any
      
      try {
        coverData = JSON.parse(row.cover_data)
      } catch {
        coverData = {
          title: row.title,
          cover_url: row.cover_url,
          year: row.year,
          season: row.season,
          episode: row.episode
        }
      }
      
      try {
        bangumiInfo = row.bangumi_info ? JSON.parse(row.bangumi_info) : undefined
      } catch {
        bangumiInfo = undefined
      }
      
      newDb.setCoverCache(row.anime_id, coverData, bangumiInfo)
    }
    
    log.info(`[Migration] Migrated ${rows.length} cover caches`)
    return rows.length
  } catch (error) {
    log.error('[Migration] Failed to migrate cover caches:', error)
    return 0
  }
}

/**
 * 迁移播放历史数据
 */
async function migratePlaybackHistory(legacyDb: Database.Database, newDb: DatabaseService): Promise<number> {
  try {
    // 检查旧表是否存在
    const tableExists = legacyDb.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' AND name='playbackhistory'
    `).get()
    
    if (!tableExists) {
      log.info('[Migration] No playbackhistory table in legacy database')
      return 0
    }
    
    const rows = legacyDb.prepare('SELECT * FROM playbackhistory').all() as any[]
    
    for (const row of rows) {
      newDb.addPlaybackHistory({
        animeId: row.anime_id,
        animeTitle: row.anime_title,
        episodeId: row.episode_id,
        episodeNum: row.episode_num,
        positionSeconds: row.position_seconds ?? 0,
        totalSeconds: row.total_seconds ?? 0,
        lastWatchedAt: row.last_watched_at ? new Date(row.last_watched_at).getTime() : Date.now(),
        coverUrl: row.cover_url
      })
    }
    
    log.info(`[Migration] Migrated ${rows.length} playback history entries`)
    return rows.length
  } catch (error) {
    log.error('[Migration] Failed to migrate playback history:', error)
    return 0
  }
}

/**
 * 迁移设置数据
 */
async function migrateSettings(legacyDb: Database.Database, newDb: DatabaseService): Promise<number> {
  try {
    // 检查旧表是否存在
    const tableExists = legacyDb.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' AND name='settings'
    `).get()
    
    if (!tableExists) {
      log.info('[Migration] No settings table in legacy database')
      return 0
    }
    
    const rows = legacyDb.prepare('SELECT * FROM settings').all() as Array<{ key: string; value: string }>
    
    for (const row of rows) {
      newDb.setSetting(row.key, row.value)
    }
    
    log.info(`[Migration] Migrated ${rows.length} settings`)
    return rows.length
  } catch (error) {
    log.error('[Migration] Failed to migrate settings:', error)
    return 0
  }
}

/**
 * 创建迁移标记文件
 */
export function markMigrationCompleted(): void {
  const markerPath = join(app.getPath('userData'), '.migration_completed')
  try {
    const fs = require('fs')
    fs.writeFileSync(markerPath, new Date().toISOString())
  } catch (error) {
    log.error('[Migration] Failed to create migration marker:', error)
  }
}

/**
 * 检查是否已完成迁移
 */
export function isMigrationCompleted(): boolean {
  const markerPath = join(app.getPath('userData'), '.migration_completed')
  return existsSync(markerPath)
}
