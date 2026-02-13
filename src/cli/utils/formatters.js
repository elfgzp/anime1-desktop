/**
 * CLI Formatters
 */

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration in milliseconds to human readable string
 */
export function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }
  return `${seconds}s`;
}

/**
 * Format date to locale string
 */
export function formatDate(date) {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  return date.toLocaleString();
}

/**
 * Format status with color
 */
export function formatStatus(status) {
  const colors = {
    pending: '\x1b[37m',    // white
    downloading: '\x1b[34m', // blue
    completed: '\x1b[32m',   // green
    failed: '\x1b[31m',      // red
    cancelled: '\x1b[33m',   // yellow
    skipped: '\x1b[90m'      // gray
  };
  
  const reset = '\x1b[0m';
  const color = colors[status] || '';
  
  return `${color}${status}${reset}`;
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str, maxLength) {
  if (!str || str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

/**
 * Pad string to fixed width
 */
export function pad(str, width) {
  str = String(str);
  if (str.length >= width) return str;
  return str + ' '.repeat(width - str.length);
}
