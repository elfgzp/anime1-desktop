#!/usr/bin/env node
/**
 * Anime1 Desktop CLI Tool
 * 
 * Provides command-line interface for managing:
 * - Auto download service
 * - Cache management
 * - Log viewing
 * - Configuration
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';

// Get package info
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packageJson = JSON.parse(readFileSync(join(__dirname, '../../package.json'), 'utf8'));

import { program } from 'commander';
import chalk from 'chalk';

// Import commands
import { autoDownloadCommands } from './commands/autoDownload.js';
import { cacheCommands } from './commands/cache.js';
import { logCommands } from './commands/logs.js';
import { configCommands } from './commands/config.js';

// ASCII Art Banner
const banner = `
${chalk.cyan('╔══════════════════════════════════════════════════════════╗')}
${chalk.cyan('║')}                    Anime1 Desktop v${packageJson.version.padEnd(10)}${chalk.cyan('║')}
${chalk.cyan('║')}                                                          ${chalk.cyan('║')}
${chalk.cyan('║')}              Command Line Interface Tool                 ${chalk.cyan('║')}
${chalk.cyan('╚══════════════════════════════════════════════════════════╝')}
`;

// Print banner if not in quiet mode
if (!process.argv.includes('-q') && !process.argv.includes('--quiet')) {
  console.log(banner);
}

program
  .name('anime1')
  .description('Anime1 Desktop CLI Tool')
  .version(packageJson.version, '-v, --version')
  .option('-q, --quiet', 'suppress banner output')
  .configureOutput({
    outputError: (str, write) => write(chalk.red(str))
  });

// Auto Download Commands
program
  .command('download')
  .alias('dl')
  .description('Manage auto downloads')
  .addCommand(autoDownloadCommands.status)
  .addCommand(autoDownloadCommands.start)
  .addCommand(autoDownloadCommands.stop)
  .addCommand(autoDownloadCommands.config)
  .addCommand(autoDownloadCommands.history)
  .addCommand(autoDownloadCommands.add);

// Cache Commands
program
  .command('cache')
  .description('Manage application cache')
  .addCommand(cacheCommands.info)
  .addCommand(cacheCommands.clear)
  .addCommand(cacheCommands.refresh);

// Log Commands
program
  .command('logs')
  .description('View and manage logs')
  .addCommand(logCommands.view)
  .addCommand(logCommands.export)
  .addCommand(logCommands.clear);

// Config Commands
program
  .command('config')
  .description('Manage application configuration')
  .addCommand(configCommands.get)
  .addCommand(configCommands.set)
  .addCommand(configCommands.list);

// Quick commands
program
  .command('status')
  .description('Show overall application status')
  .action(async () => {
    const { showStatus } = await import('./commands/status.js');
    await showStatus();
  });

program
  .command('open')
  .description('Open application data directory')
  .action(async () => {
    const { openDataDir } = await import('./commands/utils.js');
    await openDataDir();
  });

// Parse arguments
program.parse();

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
