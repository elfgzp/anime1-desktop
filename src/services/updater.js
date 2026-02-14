/**
 * Auto Updater Service using electron-updater
 * 
 * Features:
 * - Check for updates from GitHub Releases
 * - Download updates with progress tracking
 * - Silent background download
 * - Auto-install on app quit
 * 
 * Mock Testing:
 * - Set MOCK_UPDATER=true to enable mock mode
 * - Use MOCK_UPDATER_SCENARIO to set test scenario
 * - Available scenarios: no-update, has-update, check-error, download-error, downloaded
 */

import { autoUpdater } from 'electron-updater';
import { app, ipcMain, BrowserWindow } from 'electron';
import logger from 'electron-log';

// Check if mock mode is enabled
const isMockMode = process.env.MOCK_UPDATER === 'true';

// Import mock implementation if in mock mode
let mockUpdater = null;
if (isMockMode) {
  // Dynamic import to avoid loading mock code in production
  const { initMockUpdater } = await import('./updater.mock.js');
  mockUpdater = { initMockUpdater };
  logger.info('[Updater] Mock mode enabled');
}

// Configure logging
autoUpdater.logger = logger;
autoUpdater.logger.transports.file.level = 'info';

// Update configuration
const UPDATE_CONFIG = {
  // Enable automatic download (default: true)
  autoDownload: true,
  // Allow prerelease versions (default: false)
  allowPrerelease: false,
  // Check interval in ms (default: 1 hour)
  checkInterval: 60 * 60 * 1000,
};

// Helper function to format bytes
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Update state
let updateState = {
  checking: false,
  available: false,
  downloading: false,
  downloaded: false,
  error: null,
  progress: {
    percent: 0,
    bytesPerSecond: 0,
    total: 0,
    transferred: 0,
  },
  info: null, // UpdateInfo object
};

// Store the main window for sending IPC messages
let mainWindow = null;

/**
 * Send update state to renderer process
 */
function sendStatusToWindow(channel, data = {}) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('updater:' + channel, data);
  }
}

/**
 * Reset update state
 */
function resetState() {
  updateState = {
    checking: false,
    available: false,
    downloading: false,
    downloaded: false,
    error: null,
    progress: {
      percent: 0,
      bytesPerSecond: 0,
      total: 0,
      transferred: 0,
    },
    info: null,
  };
}

/**
 * Initialize auto updater
 * @param {BrowserWindow} win - Main browser window
 */
export function initUpdater(win) {
  mainWindow = win;
  
  // If in mock mode, delegate to mock implementation
  if (isMockMode && mockUpdater) {
    return mockUpdater.initMockUpdater(win);
  }

  // Configure auto updater
  autoUpdater.autoDownload = UPDATE_CONFIG.autoDownload;
  autoUpdater.allowPrerelease = UPDATE_CONFIG.allowPrerelease;

  // Event: Checking for update
  autoUpdater.on('checking-for-update', () => {
    logger.info('[Updater] Checking for update...');
    updateState.checking = true;
    updateState.error = null;
    sendStatusToWindow('checking');
  });

  // Event: Update available
  autoUpdater.on('update-available', (info) => {
    logger.info('[Updater] Update available:', info.version);
    updateState.checking = false;
    updateState.available = true;
    updateState.info = {
      version: info.version,
      releaseDate: info.releaseDate,
      releaseNotes: info.releaseNotes,
    };
    sendStatusToWindow('available', updateState.info);
  });

  // Event: Update not available
  autoUpdater.on('update-not-available', (info) => {
    logger.info('[Updater] Update not available, current:', info.version);
    updateState.checking = false;
    updateState.available = false;
    sendStatusToWindow('not-available', { version: info.version });
  });

  // Event: Download progress
  autoUpdater.on('download-progress', (progressObj) => {
    updateState.downloading = true;
    updateState.progress = {
      percent: Math.round(progressObj.percent),
      bytesPerSecond: progressObj.bytesPerSecond,
      total: progressObj.total,
      transferred: progressObj.transferred,
    };
    
    logger.debug('[Updater] Download progress:', updateState.progress.percent + '%');
    sendStatusToWindow('progress', updateState.progress);
  });

  // Event: Update downloaded
  autoUpdater.on('update-downloaded', (info) => {
    logger.info('[Updater] Update downloaded:', info.version);
    updateState.downloading = false;
    updateState.downloaded = true;
    updateState.info = {
      version: info.version,
      releaseDate: info.releaseDate,
      releaseNotes: info.releaseNotes,
    };
    sendStatusToWindow('downloaded', updateState.info);

    // Optionally install immediately (not recommended, better on quit)
    // autoUpdater.quitAndInstall();
  });

  // Event: Error
  autoUpdater.on('error', (err) => {
    logger.error('[Updater] Error:', err.message);
    updateState.checking = false;
    updateState.downloading = false;
    updateState.error = err.message;
    sendStatusToWindow('error', { message: err.message });
  });

  // Setup IPC handlers
  setupIpcHandlers();

  logger.info('[Updater] Initialized');
}

/**
 * Setup IPC handlers for updater
 */
function setupIpcHandlers() {
  // Check for updates - Returns format compatible with Python version
  ipcMain.handle('updater:check', async () => {
    try {
      resetState();
      const result = await autoUpdater.checkForUpdates();
      
      // Convert to Python version compatible format
      const updateInfo = result?.updateInfo;
      const currentVersion = app.getVersion();
      
      if (!updateInfo || updateInfo.version === currentVersion) {
        return {
          success: true,
          data: {
            has_update: false,
            current_version: currentVersion,
            latest_version: updateInfo?.version || currentVersion,
          }
        };
      }
      
      // Get download URL from update info
      const downloadUrl = updateInfo.files?.[0]?.url || 
        `https://github.com/gzp/anime1-desktop/releases/tag/v${updateInfo.version}`;
      
      return {
        success: true,
        data: {
          has_update: true,
          current_version: currentVersion,
          latest_version: updateInfo.version,
          is_prerelease: false,
          release_notes: updateInfo.releaseNotes || '',
          download_url: downloadUrl,
          asset_name: updateInfo.files?.[0]?.url?.split('/').pop() || '',
          download_size: formatBytes(updateInfo.files?.[0]?.size || 0),
          published_at: new Date().toISOString(),
        }
      };
    } catch (error) {
      logger.error('[Updater] Check failed:', error.message);
      return {
        success: false,
        error: error.message,
        error_type: 'update_check_failed',
        data: {
          has_update: false,
          current_version: app.getVersion(),
          latest_version: null,
        }
      };
    }
  });

  // Download update
  ipcMain.handle('updater:download', async () => {
    try {
      if (!updateState.available) {
        return {
          success: false,
          error: 'No update available',
        };
      }

      const result = await autoUpdater.downloadUpdate();
      return {
        success: true,
        downloadPromise: result,
      };
    } catch (error) {
      logger.error('[Updater] Download failed:', error.message);
      return {
        success: false,
        error: error.message,
      };
    }
  });

  // Install update
  ipcMain.handle('updater:install', () => {
    try {
      if (!updateState.downloaded) {
        return {
          success: false,
          error: 'Update not downloaded yet',
        };
      }

      // Quit and install
      autoUpdater.quitAndInstall();
      return { success: true };
    } catch (error) {
      logger.error('[Updater] Install failed:', error.message);
      return {
        success: false,
        error: error.message,
      };
    }
  });

  // Get current status
  ipcMain.handle('updater:status', () => {
    return {
      success: true,
      data: updateState,
    };
  });
}

/**
 * Check for updates manually
 */
export async function checkForUpdates() {
  try {
    resetState();
    const result = await autoUpdater.checkForUpdates();
    return result;
  } catch (error) {
    logger.error('[Updater] Check failed:', error.message);
    throw error;
  }
}

/**
 * Download update manually
 */
export async function downloadUpdate() {
  try {
    return await autoUpdater.downloadUpdate();
  } catch (error) {
    logger.error('[Updater] Download failed:', error.message);
    throw error;
  }
}

/**
 * Quit and install update
 */
export function quitAndInstall() {
  autoUpdater.quitAndInstall();
}

/**
 * Get current update state
 */
export function getUpdateState() {
  return { ...updateState };
}

/**
 * Set update feed URL (for testing or custom source)
 * @param {string} url - Update feed URL
 */
export function setFeedURL(url) {
  autoUpdater.setFeedURL(url);
}

/**
 * Check if running in mock mode
 */
export function isMockUpdater() {
  return isMockMode;
}

export default {
  initUpdater,
  checkForUpdates,
  downloadUpdate,
  quitAndInstall,
  getUpdateState,
  setFeedURL,
  isMockUpdater,
};
