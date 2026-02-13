/**
 * Logs CLI Commands
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { readFileSync, existsSync, statSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';
import { createReadStream } from 'fs';
import { createInterface } from 'readline';
import { promisify } from 'util';
import { pipeline } from 'stream';
import { createWriteStream } from 'fs';

const pipelineAsync = promisify(pipeline);

// Get log directory
function getLogDir() {
  return join(homedir(), 'Library', 'Logs', 'anime1-desktop-electron-forge');
}

function getLogFile() {
  return join(getLogDir(), 'anime1.log');
}

// View command
const view = new Command('view')
  .alias('v')
  .description('View application logs')
  .option('-n, --lines <number>', 'number of lines to show', '50')
  .option('-f, --follow', 'follow log output (tail mode)')
  .option('-l, --level <level>', 'filter by level (debug/info/warn/error)')
  .action(async (options) => {
    try {
      const logFile = getLogFile();
      
      if (!existsSync(logFile)) {
        console.log(chalk.yellow('No log file found'));
        return;
      }
      
      const stats = statSync(logFile);
      console.log(chalk.gray(`Log file: ${logFile} (${(stats.size / 1024).toFixed(1)} KB)\n`));
      
      if (options.follow) {
        // Tail mode
        console.log(chalk.cyan('Following logs (Ctrl+C to exit)...\n'));
        
        let lastSize = stats.size;
        
        const readNewLines = () => {
          const newStats = statSync(logFile);
          if (newStats.size > lastSize) {
            const stream = createReadStream(logFile, { start: lastSize });
            stream.on('data', chunk => {
              process.stdout.write(chunk);
            });
            lastSize = newStats.size;
          }
        };
        
        // Initial read
        const lines = parseInt(options.lines);
        const content = readFileSync(logFile, 'utf8');
        const allLines = content.split('\n');
        const lastLines = allLines.slice(-lines).join('\n');
        console.log(lastLines);
        
        // Watch for changes
        const interval = setInterval(readNewLines, 1000);
        
        // Handle Ctrl+C
        process.on('SIGINT', () => {
          clearInterval(interval);
          console.log(chalk.yellow('\n\nStopped watching logs'));
          process.exit(0);
        });
        
      } else {
        // Read last N lines
        const lines = parseInt(options.lines);
        const content = readFileSync(logFile, 'utf8');
        const allLines = content.split('\n');
        
        let filteredLines = allLines;
        
        // Filter by level if specified
        if (options.level) {
          const levelUpper = options.level.toUpperCase();
          filteredLines = allLines.filter(line => {
            return line.includes(`[${levelUpper}]`);
          });
        }
        
        const lastLines = filteredLines.slice(-lines);
        
        // Colorize output
        lastLines.forEach(line => {
          if (line.includes('[ERROR]')) {
            console.log(chalk.red(line));
          } else if (line.includes('[WARN]')) {
            console.log(chalk.yellow(line));
          } else if (line.includes('[INFO]')) {
            console.log(line);
          } else if (line.includes('[DEBUG]')) {
            console.log(chalk.gray(line));
          } else {
            console.log(line);
          }
        });
        
        console.log(chalk.gray(`\nShowing ${lastLines.length} lines`));
      }
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Export command
const exportCmd = new Command('export')
  .alias('e')
  .description('Export logs to file')
  .requiredOption('-o, --output <path>', 'output file path')
  .option('-l, --level <level>', 'filter by level')
  .action(async (options) => {
    try {
      const logFile = getLogFile();
      
      if (!existsSync(logFile)) {
        console.log(chalk.yellow('No log file found'));
        return;
      }
      
      const input = createReadStream(logFile);
      const output = createWriteStream(options.output);
      
      if (options.level) {
        // Filter by level
        const levelUpper = options.level.toUpperCase();
        const rl = createInterface({ input });
        
        for await (const line of rl) {
          if (line.includes(`[${levelUpper}]`)) {
            output.write(line + '\n');
          }
        }
        output.end();
      } else {
        // Copy entire file
        await pipelineAsync(input, output);
      }
      
      console.log(chalk.green(`✓ Logs exported to ${options.output}`));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Clear command
const clear = new Command('clear')
  .alias('c')
  .description('Clear logs')
  .option('-f, --force', 'skip confirmation')
  .action(async (options) => {
    try {
      if (!options.force) {
        const confirmed = await promptConfirm('Clear all logs?');
        if (!confirmed) {
          console.log(chalk.yellow('Cancelled'));
          return;
        }
      }
      
      const logFile = getLogFile();
      
      if (!existsSync(logFile)) {
        console.log(chalk.yellow('No log file found'));
        return;
      }
      
      // Truncate file
      const fs = await import('fs');
      fs.truncateSync(logFile, 0);
      
      console.log(chalk.green('✓ Logs cleared'));
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Helper function
async function promptConfirm(message) {
  const { default: inquirer } = await import('inquirer');
  const { confirmed } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirmed',
    message,
    default: false
  }]);
  return confirmed;
}

export const logCommands = {
  view,
  export: exportCmd,
  clear
};
