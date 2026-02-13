/**
 * Logger Service for Electron
 * 
 * Features:
 * - File logging with rotation
 * - Log level filtering
 * - Log viewing API
 * - Log clearing
 */

import { app } from 'electron';
import path from 'path';
import fs from 'fs';
import log from 'electron-log';

// Configure electron-log
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

// Log levels
export const LogLevel = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
};

// Level priorities for filtering
const LEVEL_PRIORITY = {
  [LogLevel.DEBUG]: 0,
  [LogLevel.INFO]: 1,
  [LogLevel.WARN]: 2,
  [LogLevel.ERROR]: 3,
};

/**
 * Get logs directory
 */
export function getLogsDirectory() {
  const userDataPath = app.getPath('userData');
  const logsPath = path.join(userDataPath, 'logs');
  
  if (!fs.existsSync(logsPath)) {
    fs.mkdirSync(logsPath, { recursive: true });
  }
  
  return logsPath;
}

/**
 * Get main log file path
 */
export function getLogFilePath() {
  return path.join(getLogsDirectory(), 'app.log');
}

/**
 * Parse log line
 * Format: "2024-01-15 10:30:45.123 [INFO] message"
 */
function parseLogLine(line) {
  line = line.trim();
  if (!line) return null;

  try {
    // Try to parse standard format
    // electron-log format: "[2024-01-15 10:30:45.123] [INFO] message"
    const bracketMatch = line.match(/^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s+\[(\w+)\]\s+(.+)$/);
    if (bracketMatch) {
      return {
        timestamp: bracketMatch[1],
        level: bracketMatch[2].toUpperCase(),
        message: bracketMatch[3].trim(),
      };
    }

    // Alternative format: "2024-01-15 10:30:45.123 [INFO] message"
    const spaceMatch = line.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+\[(\w+)\]\s+(.+)$/);
    if (spaceMatch) {
      return {
        timestamp: spaceMatch[1].replace(',', '.'),
        level: spaceMatch[2].toUpperCase(),
        message: spaceMatch[3].trim(),
      };
    }

    // Non-standard format
    return {
      timestamp: new Date().toISOString(),
      level: 'RAW',
      message: line,
    };
  } catch (error) {
    return {
      timestamp: new Date().toISOString(),
      level: 'PARSE_ERROR',
      message: line,
    };
  }
}

/**
 * Get logs with filtering
 * 
 * @param {Object} options
 * @param {number} options.lines - Number of lines to return (default: 100, max: 1000)
 * @param {string} options.level - Filter by log level (DEBUG, INFO, WARN, ERROR)
 * @param {string} options.search - Search term in message
 * @returns {Object} - { logs: Array, totalLines: number }
 */
export function getLogs(options = {}) {
  const lines = Math.min(Math.max(options.lines || 100, 10), 1000);
  const levelFilter = options.level?.toUpperCase();
  const searchTerm = options.search?.toLowerCase();

  const logFile = getLogFilePath();
  const logs = [];

  if (!fs.existsSync(logFile)) {
    return { logs: [], totalLines: 0, message: '日志文件不存在' };
  }

  try {
    // Read log file
    const content = fs.readFileSync(logFile, 'utf-8');
    const allLines = content.split('\n').filter(line => line.trim());
    
    // Process from newest to oldest
    for (let i = allLines.length - 1; i >= 0; i--) {
      const line = allLines[i];
      const parsed = parseLogLine(line);
      
      if (!parsed) continue;

      // Apply level filter
      if (levelFilter && parsed.level !== levelFilter) {
        continue;
      }

      // Apply search filter
      if (searchTerm && !parsed.message.toLowerCase().includes(searchTerm)) {
        continue;
      }

      logs.push(parsed);

      // Stop when we have enough
      if (logs.length >= lines) {
        break;
      }
    }

    // Reverse to get chronological order
    logs.reverse();

    return {
      logs,
      totalLines: logs.length,
      fileLines: allLines.length,
    };
  } catch (error) {
    console.error('[Logger] Error reading logs:', error);
    return { logs: [], totalLines: 0, error: error.message };
  }
}

/**
 * Get log statistics
 */
export function getLogStats() {
  const logFile = getLogFilePath();
  
  if (!fs.existsSync(logFile)) {
    return {
      totalLines: 0,
      fileSize: 0,
      byLevel: {},
    };
  }

  try {
    const stats = fs.statSync(logFile);
    const content = fs.readFileSync(logFile, 'utf-8');
    const lines = content.split('\n').filter(line => line.trim());

    const byLevel = {};
    lines.forEach(line => {
      const parsed = parseLogLine(line);
      if (parsed) {
        const level = parsed.level;
        byLevel[level] = (byLevel[level] || 0) + 1;
      }
    });

    return {
      totalLines: lines.length,
      fileSize: stats.size,
      byLevel,
    };
  } catch (error) {
    console.error('[Logger] Error getting stats:', error);
    return { totalLines: 0, fileSize: 0, byLevel: {}, error: error.message };
  }
}

/**
 * Clear logs
 */
export function clearLogs() {
  const logFile = getLogFilePath();
  
  try {
    if (fs.existsSync(logFile)) {
      // Truncate file
      fs.writeFileSync(logFile, '', 'utf-8');
      log.info('Logs cleared');
    }
    return { success: true };
  } catch (error) {
    console.error('[Logger] Error clearing logs:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Export logs to file
 */
export function exportLogs(exportPath) {
  const logFile = getLogFilePath();
  
  try {
    if (!fs.existsSync(logFile)) {
      return { success: false, error: '日志文件不存在' };
    }

    fs.copyFileSync(logFile, exportPath);
    return { success: true, path: exportPath };
  } catch (error) {
    console.error('[Logger] Error exporting logs:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Get log file info
 */
export function getLogFileInfo() {
  const logFile = getLogFilePath();
  
  if (!fs.existsSync(logFile)) {
    return {
      exists: false,
      path: logFile,
      size: 0,
      modified: null,
    };
  }

  const stats = fs.statSync(logFile);
  return {
    exists: true,
    path: logFile,
    size: stats.size,
    modified: stats.mtime.toISOString(),
  };
}

/**
 * Logger wrapper with structured logging support
 */
export class Logger {
  constructor(scope = 'app') {
    this.scope = scope;
  }

  debug(message, meta = {}) {
    log.debug(`[${this.scope}] ${message}`, meta);
  }

  info(message, meta = {}) {
    log.info(`[${this.scope}] ${message}`, meta);
  }

  warn(message, meta = {}) {
    log.warn(`[${this.scope}] ${message}`, meta);
  }

  error(message, meta = {}) {
    log.error(`[${this.scope}] ${message}`, meta);
  }
}

// Export default logger
export const logger = new Logger('main');

export default {
  LogLevel,
  Logger,
  logger,
  getLogs,
  getLogStats,
  clearLogs,
  exportLogs,
  getLogFileInfo,
  getLogsDirectory,
  getLogFilePath,
};
