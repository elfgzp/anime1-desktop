/**
 * Config CLI Commands
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { settingsDB } from '../../services/database.js';
import { promptInput, promptSelect } from '../utils/prompts.js';

// Get command
const get = new Command('get')
  .alias('g')
  .description('Get configuration value')
  .argument('<key>', 'configuration key')
  .action(async (key) => {
    try {
      const value = await settingsDB.get(key);
      
      if (value === null || value === undefined) {
        console.log(chalk.yellow(`Key '${key}' not found`));
        return;
      }
      
      if (typeof value === 'object') {
        console.log(JSON.stringify(value, null, 2));
      } else {
        console.log(`${chalk.cyan(key)}: ${value}`);
      }
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Set command
const set = new Command('set')
  .alias('s')
  .description('Set configuration value')
  .argument('<key>', 'configuration key')
  .argument('<value>', 'configuration value')
  .option('-j, --json', 'parse value as JSON')
  .action(async (key, value, options) => {
    try {
      let parsedValue = value;
      
      if (options.json) {
        parsedValue = JSON.parse(value);
      } else if (value === 'true') {
        parsedValue = true;
      } else if (value === 'false') {
        parsedValue = false;
      } else if (!isNaN(value) && value !== '') {
        parsedValue = Number(value);
      }
      
      await settingsDB.set(key, parsedValue);
      console.log(chalk.green(`✓ Set ${key} = ${JSON.stringify(parsedValue)}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// List command
const list = new Command('list')
  .alias('ls')
  .description('List all configuration')
  .option('-a, --all', 'show all settings including internal')
  .action(async (options) => {
    try {
      // Get all settings
      const settings = await settingsDB.getAll?.() || {};
      
      // Common settings to display
      const commonSettings = [
        'theme',
        'download_path',
        'auto_download_enabled',
        'check_update_on_startup',
        'window_width',
        'window_height'
      ];
      
      console.log(chalk.cyan('\n' + '='.repeat(50)));
      console.log(chalk.bold('应用配置'));
      console.log(chalk.cyan('='.repeat(50)));
      
      const table = new Table({
        head: [chalk.gray('Key'), chalk.gray('Value')],
        colWidths: [30, 50]
      });
      
      const keysToShow = options.all ? Object.keys(settings) : commonSettings;
      
      keysToShow.forEach(key => {
        if (key in settings) {
          const value = settings[key];
          const displayValue = typeof value === 'object' 
            ? JSON.stringify(value).substring(0, 40)
            : String(value);
          table.push([key, displayValue]);
        }
      });
      
      console.log(table.toString());
      console.log(chalk.cyan('='.repeat(50) + '\n'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

export const configCommands = {
  get,
  set,
  list
};
