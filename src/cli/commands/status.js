/**
 * Overall Status Command
 */

import chalk from 'chalk';
import Table from 'cli-table3';
import { getCacheStats } from '../../services/coverCache.js';
import { getCacheStats as getPlaylistCacheStats } from '../../services/playlistCache.js';
import { getAutoDownloadService } from '../../services/autoDownload.js';

export async function showStatus() {
  try {
    console.log(chalk.cyan('\n' + '='.repeat(60)));
    console.log(chalk.bold('📊 Anime1 Desktop 整体状态'));
    console.log(chalk.cyan('='.repeat(60)));
    
    // Auto Download Status
    console.log(chalk.yellow('\n📥 自动下载服务:'));
    try {
      const service = getAutoDownloadService();
      const config = await service.getConfig();
      const downloads = await service.getAllDownloads();
      
      console.log(`  状态: ${config?.enabled ? chalk.green('已启用') : chalk.red('已禁用')}`);
      console.log(`  下载路径: ${config?.download_path || chalk.gray('未设置')}`);
      
      const statusCounts = downloads.reduce((acc, d) => {
        acc[d.status] = (acc[d.status] || 0) + 1;
        return acc;
      }, {});
      
      console.log(`  待下载: ${statusCounts.pending || 0} | 下载中: ${statusCounts.downloading || 0} | 已完成: ${statusCounts.completed || 0} | 失败: ${statusCounts.failed || 0}`);
    } catch (error) {
      console.log(chalk.red(`  错误: ${error.message}`));
    }
    
    // Cache Status
    console.log(chalk.yellow('\n💾 缓存状态:'));
    try {
      const coverStats = getCacheStats();
      const playlistStats = getPlaylistCacheStats();
      
      console.log(`  封面缓存: ${coverStats.count} 条`);
      console.log(`  番剧列表: ${playlistStats.animeList?.cached ? (playlistStats.animeList.valid ? chalk.green('有效') : chalk.yellow('已过期')) : chalk.gray('未缓存')}`);
      console.log(`  番剧详情: ${playlistStats.animeDetails?.validCount || 0}/${playlistStats.animeDetails?.count || 0} 有效`);
      console.log(`  剧集缓存: ${playlistStats.episodes?.validCount || 0}/${playlistStats.episodes?.count || 0} 有效`);
    } catch (error) {
      console.log(chalk.red(`  错误: ${error.message}`));
    }
    
    // Log Status
    console.log(chalk.yellow('\n📝 日志状态:'));
    try {
      const { existsSync, statSync } = await import('fs');
      const { join } = await import('path');
      const { homedir } = await import('os');
      
      const logFile = join(homedir(), 'Library', 'Logs', 'anime1-desktop-electron-forge', 'anime1.log');
      
      if (existsSync(logFile)) {
        const stats = statSync(logFile);
        const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
        console.log(`  日志文件: ${sizeMB} MB`);
        console.log(`  最后修改: ${stats.mtime.toLocaleString()}`);
      } else {
        console.log(chalk.gray('  日志文件不存在'));
      }
    } catch (error) {
      console.log(chalk.red(`  错误: ${error.message}`));
    }
    
    console.log(chalk.cyan('='.repeat(60) + '\n'));
    
  } catch (error) {
    console.error(chalk.red('Error:'), error.message);
    process.exit(1);
  }
}
