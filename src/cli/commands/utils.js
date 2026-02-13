/**
 * CLI Utility Commands
 */

import { spawn } from 'child_process';
import { join } from 'path';
import { homedir } from 'os';
import chalk from 'chalk';

export async function openDataDir() {
  const dataDir = join(homedir(), 'Library', 'Application Support', 'anime1-desktop-electron-forge');
  
  console.log(chalk.cyan(`Opening: ${dataDir}`));
  
  const platform = process.platform;
  let command;
  
  switch (platform) {
    case 'darwin':
      command = 'open';
      break;
    case 'win32':
      command = 'explorer';
      break;
    case 'linux':
      command = 'xdg-open';
      break;
    default:
      console.log(chalk.yellow(`Please open manually: ${dataDir}`));
      return;
  }
  
  spawn(command, [dataDir], { detached: true });
  console.log(chalk.green('✓ Opened data directory'));
}
