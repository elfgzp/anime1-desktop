/**
 * Auto Download CLI Commands
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { getAutoDownloadService } from '../../services/autoDownload.js';
import { formatBytes, formatDuration } from '../utils/formatters.js';
import { promptConfirm, promptInput, promptSelect } from '../utils/prompts.js';

// Status command
const status = new Command('status')
  .alias('s')
  .description('Show auto download status')
  .action(async () => {
    try {
      const service = getAutoDownloadService();
      const config = await service.getConfig();
      const downloads = await service.getAllDownloads();
      
      console.log(chalk.cyan('\n' + '='.repeat(50)));
      console.log(chalk.bold('自动下载状态'));
      console.log(chalk.cyan('='.repeat(50)));
      
      // Service status
      const isEnabled = config?.enabled || false;
      console.log(`服务状态: ${isEnabled ? chalk.green('已启用') : chalk.red('已禁用')}`);
      console.log(`下载路径: ${chalk.yellow(config?.download_path || '未设置')}`);
      console.log(`并发数量: ${config?.max_concurrent || 2}`);
      console.log(`检查间隔: ${config?.check_interval_hours || 24} 小时`);
      
      // Filter settings
      if (config?.filter) {
        console.log(chalk.cyan('\n筛选条件:'));
        const filter = config.filter;
        if (filter.year_start || filter.year_end) {
          console.log(`  年份: ${filter.year_start || '不限'} - ${filter.year_end || '不限'}`);
        }
        if (filter.seasons?.length) {
          console.log(`  季度: ${filter.seasons.join(', ')}`);
        }
        if (filter.min_episodes) {
          console.log(`  最少集数: ${filter.min_episodes}`);
        }
        if (filter.include_patterns?.length) {
          console.log(`  包含模式: ${filter.include_patterns.join(', ')}`);
        }
        if (filter.exclude_patterns?.length) {
          console.log(`  排除模式: ${filter.exclude_patterns.join(', ')}`);
        }
      }
      
      // Download statistics
      const statusCounts = downloads.reduce((acc, d) => {
        acc[d.status] = (acc[d.status] || 0) + 1;
        return acc;
      }, {});
      
      console.log(chalk.cyan('\n下载统计:'));
      console.log(`  ${chalk.gray('待下载:')} ${statusCounts.pending || 0}`);
      console.log(`  ${chalk.blue('下载中:')} ${statusCounts.downloading || 0}`);
      console.log(`  ${chalk.green('已完成:')} ${statusCounts.completed || 0}`);
      console.log(`  ${chalk.red('失败:')} ${statusCounts.failed || 0}`);
      console.log(`  ${chalk.yellow('已取消:')} ${statusCounts.cancelled || 0}`);
      
      // Recent downloads
      const recentCompleted = downloads
        .filter(d => d.status === 'completed')
        .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))
        .slice(0, 5);
      
      if (recentCompleted.length > 0) {
        console.log(chalk.cyan('\n最近完成:'));
        const table = new Table({
          head: [chalk.gray('番剧'), chalk.gray('集数'), chalk.gray('大小'), chalk.gray('完成时间')],
          colWidths: [30, 10, 12, 20]
        });
        
        recentCompleted.forEach(d => {
          table.push([
            d.anime_title.substring(0, 28),
            d.episode_num,
            formatBytes(d.total_bytes),
            new Date(d.completed_at).toLocaleString()
          ]);
        });
        console.log(table.toString());
      }
      
      console.log(chalk.cyan('='.repeat(50) + '\n'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Start command
const start = new Command('start')
  .description('Start auto download service')
  .action(async () => {
    try {
      const service = getAutoDownloadService();
      await service.init();
      await service.startService();
      console.log(chalk.green('✓ Auto download service started'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Stop command
const stop = new Command('stop')
  .description('Stop auto download service')
  .action(async () => {
    try {
      const service = getAutoDownloadService();
      await service.stopService();
      console.log(chalk.green('✓ Auto download service stopped'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Config command
const config = new Command('config')
  .alias('cfg')
  .description('Configure auto download settings')
  .option('-p, --path <path>', 'set download path')
  .option('-c, --concurrent <number>', 'set max concurrent downloads', parseInt)
  .option('-i, --interval <hours>', 'set check interval in hours', parseInt)
  .option('--enable', 'enable auto download')
  .option('--disable', 'disable auto download')
  .action(async (options) => {
    try {
      const service = getAutoDownloadService();
      let config = await service.getConfig() || {};
      
      // Interactive mode if no options provided
      if (Object.keys(options).length === 0) {
        console.log(chalk.cyan('Interactive configuration mode\n'));
        
        config.download_path = await promptInput('Download path:', config.download_path);
        config.max_concurrent = parseInt(await promptInput('Max concurrent:', config.max_concurrent || 2));
        config.check_interval_hours = parseInt(await promptInput('Check interval (hours):', config.check_interval_hours || 24));
        config.enabled = await promptConfirm('Enable auto download?', config.enabled);
      } else {
        // Command line options
        if (options.path) config.download_path = options.path;
        if (options.concurrent) config.max_concurrent = options.concurrent;
        if (options.interval) config.check_interval_hours = options.interval;
        if (options.enable) config.enabled = true;
        if (options.disable) config.enabled = false;
      }
      
      await service.updateConfig(config);
      console.log(chalk.green('✓ Configuration updated'));
      
      // Show updated config
      console.log(chalk.cyan('\nCurrent settings:'));
      console.log(`  Download path: ${config.download_path}`);
      console.log(`  Max concurrent: ${config.max_concurrent}`);
      console.log(`  Check interval: ${config.check_interval_hours} hours`);
      console.log(`  Enabled: ${config.enabled ? 'Yes' : 'No'}`);
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// History command
const history = new Command('history')
  .alias('h')
  .description('View download history')
  .option('-l, --limit <number>', 'number of records to show', '20')
  .option('-s, --status <status>', 'filter by status (pending/downloading/completed/failed)')
  .action(async (options) => {
    try {
      const service = getAutoDownloadService();
      const downloads = await service.getAllDownloads();
      
      let filtered = downloads;
      if (options.status) {
        filtered = downloads.filter(d => d.status === options.status);
      }
      
      // Sort by creation time (newest first)
      filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      const limit = parseInt(options.limit);
      const results = filtered.slice(0, limit);
      
      if (results.length === 0) {
        console.log(chalk.yellow('No downloads found'));
        return;
      }
      
      const table = new Table({
        head: [
          chalk.gray('ID'),
          chalk.gray('番剧'),
          chalk.gray('集数'),
          chalk.gray('状态'),
          chalk.gray('进度'),
          chalk.gray('创建时间')
        ],
        style: { head: ['cyan'] }
      });
      
      results.forEach(d => {
        const statusColor = {
          pending: chalk.gray,
          downloading: chalk.blue,
          completed: chalk.green,
          failed: chalk.red,
          cancelled: chalk.yellow
        }[d.status] || chalk.white;
        
        const progress = d.status === 'completed' 
          ? '100%' 
          : `${Math.round((d.downloaded_bytes / d.total_bytes) * 100) || 0}%`;
        
        table.push([
          d.id.substring(0, 8),
          d.anime_title.substring(0, 25),
          d.episode_num,
          statusColor(d.status),
          progress,
          new Date(d.created_at).toLocaleDateString()
        ]);
      });
      
      console.log(table.toString());
      console.log(chalk.gray(`\nShowing ${results.length} of ${filtered.length} downloads`));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Add manual download command
const add = new Command('add')
  .description('Add a manual download')
  .requiredOption('-a, --anime <title>', 'anime title')
  .requiredOption('-e, --episode <number>', 'episode number')
  .requiredOption('-u, --url <url>', 'video URL')
  .action(async (options) => {
    try {
      const service = getAutoDownloadService();
      
      const anime = {
        id: `manual-${Date.now()}`,
        title: options.anime
      };
      
      const episode = {
        id: `ep-${Date.now()}`,
        num: options.episode,
        title: `第${options.episode}集`
      };
      
      const downloadId = await service.startDownload(anime, episode, options.url);
      console.log(chalk.green(`✓ Download added: ${downloadId}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

export const autoDownloadCommands = {
  status,
  start,
  stop,
  config,
  history,
  add
};
