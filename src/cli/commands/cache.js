/**
 * Cache CLI Commands
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { getCacheStats, clearAllCovers } from '../../services/coverCache.js';
import { 
  getCacheStats as getPlaylistCacheStats, 
  clearAllCache as clearPlaylistCache,
  invalidateAnimeList
} from '../../services/playlistCache.js';
import { cacheDB } from '../../services/database.js';
import { promptConfirm } from '../utils/prompts.js';
import { formatBytes } from '../utils/formatters.js';

// Info command
const info = new Command('info')
  .alias('i')
  .description('Show cache information')
  .action(async () => {
    try {
      console.log(chalk.cyan('\n' + '='.repeat(50)));
      console.log(chalk.bold('缓存信息'));
      console.log(chalk.cyan('='.repeat(50)));
      
      // Cover cache
      const coverStats = getCacheStats();
      console.log(chalk.yellow('\n📁 封面缓存:'));
      console.log(`  缓存数量: ${coverStats.count} 条`);
      
      // Playlist cache
      const playlistStats = getPlaylistCacheStats();
      console.log(chalk.yellow('\n📋 播放列表缓存:'));
      console.log(`  番剧列表: ${playlistStats.animeList?.cached ? '已缓存' : '未缓存'}`);
      if (playlistStats.animeList?.cached) {
        console.log(`    - 条目数: ${playlistStats.animeList.itemCount}`);
        console.log(`    - 状态: ${playlistStats.animeList.valid ? chalk.green('有效') : chalk.red('已过期')}`);
      }
      console.log(`  番剧详情: ${playlistStats.animeDetails?.count || 0} 条 (${playlistStats.animeDetails?.validCount || 0} 有效)`);
      console.log(`  剧集缓存: ${playlistStats.episodes?.count || 0} 条 (${playlistStats.episodes?.validCount || 0} 有效)`);
      
      // TTL info
      console.log(chalk.yellow('\n⏱️  TTL 设置:'));
      console.log(`  番剧列表: ${Math.round(playlistStats.ttl?.animeList / 60000)} 分钟`);
      console.log(`  番剧详情: ${Math.round(playlistStats.ttl?.animeDetail / 60000)} 分钟`);
      console.log(`  剧集缓存: ${Math.round(playlistStats.ttl?.episodes / 60000)} 分钟`);
      
      console.log(chalk.cyan('='.repeat(50) + '\n'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Clear command
const clear = new Command('clear')
  .alias('c')
  .description('Clear cache')
  .option('-a, --all', 'clear all cache')
  .option('-c, --covers', 'clear cover cache')
  .option('-p, --playlist', 'clear playlist cache')
  .option('-l, --list', 'clear anime list cache only')
  .option('-f, --force', 'skip confirmation')
  .action(async (options) => {
    try {
      // If no specific option, default to all
      if (!options.covers && !options.playlist && !options.list) {
        options.all = true;
      }
      
      // Confirm unless --force
      if (!options.force) {
        const targets = [];
        if (options.covers || options.all) targets.push('封面缓存');
        if (options.playlist || options.all) targets.push('播放列表缓存');
        if (options.list) targets.push('番剧列表缓存');
        
        const confirmed = await promptConfirm(`Clear ${targets.join(', ')}?`);
        if (!confirmed) {
          console.log(chalk.yellow('Cancelled'));
          return;
        }
      }
      
      let clearedCount = 0;
      
      // Clear cover cache
      if (options.covers || options.all) {
        const count = clearAllCovers();
        console.log(chalk.green(`✓ Cleared ${count} cover cache entries`));
        clearedCount += count;
      }
      
      // Clear playlist cache
      if (options.playlist || options.all) {
        const stats = clearPlaylistCache();
        if (stats) {
          console.log(chalk.green(`✓ Cleared playlist cache:`));
          console.log(`  - Anime list: ${stats.animeList}`);
          console.log(`  - Anime details: ${stats.animeDetails}`);
          console.log(`  - Episodes: ${stats.episodes}`);
          clearedCount += stats.animeDetails + stats.episodes;
        }
      }
      
      // Clear anime list only
      if (options.list) {
        invalidateAnimeList();
        console.log(chalk.green('✓ Invalidated anime list cache'));
        clearedCount++;
      }
      
      console.log(chalk.cyan(`\nTotal cleared: ${clearedCount} entries`));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Refresh command
const refresh = new Command('refresh')
  .alias('r')
  .description('Refresh cache')
  .option('-l, --list', 'refresh anime list')
  .option('-a, --all', 'refresh all')
  .action(async (options) => {
    try {
      if (options.list || options.all) {
        console.log(chalk.cyan('Refreshing anime list...'));
        invalidateAnimeList();
        
        // Re-fetch the list
        const { animeScraper } = await import('../../services/scraper.js');
        await animeScraper.getList(1);
        
        console.log(chalk.green('✓ Anime list refreshed'));
      }
      
      if (!options.list && !options.all) {
        console.log(chalk.yellow('Use --list to refresh anime list or --all to refresh all cache'));
      }
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

export const cacheCommands = {
  info,
  clear,
  refresh
};
