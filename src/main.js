import { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage } from 'electron';
import started from 'electron-squirrel-startup';
import path from 'path';
import os from 'os';
import fs from 'fs';

import { initDatabase, favoritesDB, playbackDB, settingsDB, cacheDB } from './services/database.js';
import { initCoverCache, getCachedBangumiInfo, setCachedBangumiInfo, clearAllCovers } from './services/coverCache.js';
import { animeScraper } from './services/scraper.js';
import { getCoverUrl, getBangumiInfo } from './services/bangumi.js';
import { getVideoInfo, streamVideo } from './services/videoProxy.js';
import { proxyHlsPlaylist, proxyVideoStream } from './services/hlsProxy.js';
import { initUpdater } from './services/updater.js';
import { getAutoDownloadService } from './services/autoDownload.js';
import { getPerformanceService } from './services/performance.js';

// Enable remote debugging for MCP
app.commandLine.appendSwitch('remote-debugging-port', '9222');

// Disable CORS for video playback
app.commandLine.appendSwitch('disable-web-security');
app.commandLine.appendSwitch('disable-features', 'CrossSiteDocumentBlockingIfIsolating');

// Preload script path - use Electron Forge's webpack entry
const preloadPath = MAIN_WINDOW_PRELOAD_WEBPACK_ENTRY;
console.log('[Main] Preload path:', preloadPath);

if (started) app.quit();

// Initialize database on app ready
let dbInitialized = false;

async function initializeApp() {
  if (!dbInitialized) {
    await initDatabase();
    dbInitialized = true;
  }
  
  // Initialize cover cache
  initCoverCache();
  
  // Initialize auto download service
  const autoDownloadService = getAutoDownloadService();
  await autoDownloadService.init();
  
  // Initialize performance service
  const performanceService = getPerformanceService();
  await performanceService.init();
}

// Window state management
let mainWindow = null;
let tray = null;
const windowState = {
  width: 1280,
  height: 800,
  maximized: false,
};

// Load window state from settings
async function loadWindowState() {
  try {
    const savedState = await settingsDB.get('windowState');
    if (savedState) {
      windowState.width = savedState.width || 1280;
      windowState.height = savedState.height || 800;
      windowState.maximized = savedState.maximized || false;
    }
  } catch (error) {
    console.log('[Main] No saved window state');
  }
}

// Save window state
async function saveWindowState() {
  if (!mainWindow) return;
  
  try {
    const bounds = mainWindow.getBounds();
    const state = {
      width: bounds.width,
      height: bounds.height,
      maximized: mainWindow.isMaximized(),
    };
    await settingsDB.set('windowState', state);
  } catch (error) {
    console.error('[Main] Failed to save window state:', error);
  }
}

// Get logs directory
function getLogsDirectory() {
  const userDataPath = app.getPath('userData');
  const logsPath = path.join(userDataPath, 'logs');
  
  // Ensure directory exists
  if (!fs.existsSync(logsPath)) {
    fs.mkdirSync(logsPath, { recursive: true });
  }
  
  return logsPath;
}

// Create system tray
function createTray() {
  let icon;
  
  try {
    // Try PNG first (converted from icns)
    const iconPath = path.join(process.cwd(), 'app-icon.png');
    
    if (fs.existsSync(iconPath)) {
      console.log('[Tray] Loading icon:', iconPath);
      icon = nativeImage.createFromPath(iconPath);
      
      if (icon.isEmpty()) {
        console.log('[Tray] Warning: Icon is empty');
        icon = nativeImage.createEmpty();
      } else {
        // Resize to proper tray size - must be small for macOS
        const size = icon.getSize();
        console.log('[Tray] Original size:', size.width, 'x', size.height);
        
        // macOS tray icons should be 16x16 points
        const resized = icon.resize({ width: 16, height: 16 });
        if (!resized.isEmpty()) {
          icon = resized;
          console.log('[Tray] Resized to 16x16');
        }
        
        // Note: Not using setTemplateImage to keep the colored icon visible
        // icon.setTemplateImage(true);
      }
    } else {
      console.log('[Tray] Icon not found');
      icon = nativeImage.createEmpty();
    }
  } catch (e) {
    console.log('[Tray] Error:', e.message);
    icon = nativeImage.createEmpty();
  }
  
  console.log('[Tray] Creating tray...');
  tray = new Tray(icon);
  console.log('[Tray] Tray created');
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示窗口',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: '退出',
      click: () => {
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('Anime1 Desktop');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });
}

// IPC Handlers for Anime
ipcMain.handle('anime:list', async (event, { page = 1 } = {}) => {
  try {
    return await animeScraper.getList(page);
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('anime:detail', async (event, { id }) => {
  try {
    return await animeScraper.getDetail(id);
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('anime:episodes', async (event, { id }) => {
  try {
    return await animeScraper.getEpisodes(id);
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('anime:search', async (event, { keyword, page = 1 }) => {
  try {
    return await animeScraper.search(keyword, page);
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('anime:getCover', async (event, { id, title }) => {
  try {
    const coverUrl = await getCoverUrl(title);
    return { success: true, data: { coverUrl } };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Get Bangumi info (with cache)
ipcMain.handle('anime:getBangumiInfo', async (event, { id, title }) => {
  try {
    // Check cache first
    const cached = getCachedBangumiInfo(id);
    if (cached) {
      console.log('[Main] Bangumi info cache hit for:', id);
      return { success: true, data: cached };
    }
    
    // Fetch from Bangumi
    const info = await getBangumiInfo(title, id);
    if (info) {
      // Save to cache
      setCachedBangumiInfo(id, info);
      return { success: true, data: info };
    }
    
    return { success: true, data: null };
  } catch (error) {
    console.error('[Main] Error getting Bangumi info:', error.message);
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Favorites
ipcMain.handle('favorite:list', async () => {
  try {
    const data = await favoritesDB.list();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('favorite:add', async (event, { animeId }) => {
  try {
    const detail = await animeScraper.getDetail(animeId);
    if (!detail.success) {
      return detail;
    }
    
    await favoritesDB.add({
      id: animeId,
      title: detail.data.anime.title,
      episode: detail.data.episodes.length,
      coverUrl: detail.data.anime.cover_url
    });
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('favorite:remove', async (event, { animeId }) => {
  try {
    await favoritesDB.remove(animeId);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Settings
ipcMain.handle('settings:get', async (event, { key }) => {
  try {
    const value = await settingsDB.get(key);
    return { success: true, data: value };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('settings:set', async (event, { key, value }) => {
  try {
    await settingsDB.set(key, value);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Playback History
ipcMain.handle('playback:update', async (event, data) => {
  try {
    await playbackDB.update(data);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('playback:list', async (event, { limit = 50 }) => {
  try {
    const data = await playbackDB.list(limit);
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('playback:episode', async (event, { animeId, episodeId }) => {
  try {
    const data = await playbackDB.getEpisodeProgress(animeId, episodeId);
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Video Proxy
ipcMain.handle('video:getInfo', async (event, { url }) => {
  try {
    const result = await getVideoInfo(url);
    
    // Set cookies for video domain to enable playback
    if (result.success && result.cookies && result.url) {
      const videoUrl = new URL(result.url);
      const cookieDomain = videoUrl.hostname;
      
      for (const [name, value] of Object.entries(result.cookies)) {
        await mainWindow.webContents.session.cookies.set({
          url: result.url,
          name: name,
          value: value,
          domain: cookieDomain,
          path: '/',
          secure: true,
          httpOnly: false,
          sameSite: 'no_restriction'
        });
      }
      console.log('[Main] Cookies set for video domain:', cookieDomain);
    }
    
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for HLS Proxy
ipcMain.handle('hls:proxyPlaylist', async (event, { url, cookies }) => {
  try {
    const result = await proxyHlsPlaylist(url, cookies);
    return result;
  } catch (error) {
    console.error('[Main] HLS proxy error:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('hls:proxyVideo', async (event, { url, cookies, range }) => {
  try {
    const result = await proxyVideoStream(url, { cookies, range });
    return result;
  } catch (error) {
    console.error('[Main] Video stream proxy error:', error);
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Cache
ipcMain.handle('cache:info', async () => {
  try {
    const info = await cacheDB.getInfo();
    return { success: true, data: info };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('cache:clear', async (event, { type }) => {
  try {
    let clearedCount = 0;
    const messageParts = [];
    
    if (type === 'covers' || type === 'all') {
      const coverCount = clearAllCovers();
      clearedCount += coverCount;
      messageParts.push(`${coverCount} 条封面缓存`);
    }
    
    if (type === 'all') {
      // Clear playback history
      playbackDB.clearAll();
      messageParts.push('播放记录');
    }
    
    const message = messageParts.length > 0 ? `已清理 ${messageParts.join(' + ')}` : '没有需要清理的缓存';
    
    return { 
      success: true, 
      message,
      data: { cleared_count: clearedCount }
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Shell operations
ipcMain.handle('shell:openPath', async (event, { path: targetPath }) => {
  try {
    const result = await shell.openPath(targetPath);
    return { success: result === '', error: result || null };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('shell:openExternal', async (event, { url }) => {
  try {
    await shell.openExternal(url);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('shell:openLogsFolder', async () => {
  try {
    const logsPath = getLogsDirectory();
    const result = await shell.openPath(logsPath);
    return { success: result === '', error: result || null, path: logsPath };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Logs
import { getLogs, getLogStats, clearLogs, exportLogs, getLogFileInfo } from './services/logger.js';

ipcMain.handle('logs:get', async (event, options) => {
  try {
    const result = getLogs(options);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('logs:getStats', async () => {
  try {
    const stats = getLogStats();
    return { success: true, stats };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('logs:clear', async () => {
  try {
    const result = clearLogs();
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('logs:export', async (event, exportPath) => {
  try {
    const result = exportLogs(exportPath);
    return { success: true, ...result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('logs:getFileInfo', async () => {
  try {
    const info = getLogFileInfo();
    return { success: true, info };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Window state
ipcMain.handle('window:getState', async () => {
  return { success: true, data: windowState };
});

ipcMain.handle('window:saveState', async (event, state) => {
  try {
    await settingsDB.set('windowState', state);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for App info
// Match Python version format from src/_version.py and src/config.py
const APP_VERSION = '0.1.0';
const GITHUB_REPO_OWNER = 'elfgzp';
const GITHUB_REPO_NAME = 'anime1-desktop';

ipcMain.handle('app:getInfo', () => {
  return {
    success: true,
    data: {
      version: APP_VERSION,
      channel: 'stable',
      repository: `https://github.com/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}`,
      repo_owner: GITHUB_REPO_OWNER,
      repo_name: GITHUB_REPO_NAME,
      // Additional Electron-specific info (not in Python version)
      electronVersion: process.versions.electron,
      chromeVersion: process.versions.chrome,
      nodeVersion: process.versions.node,
      platform: os.platform(),
      arch: os.arch(),
    }
  };
});

// IPC Handlers for Auto Download
const autoDownloadService = getAutoDownloadService();

ipcMain.handle('autoDownload:getConfig', async () => {
  try {
    const config = autoDownloadService.getConfig();
    return { success: true, data: config };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:updateConfig', async (event, config) => {
  try {
    await autoDownloadService.updateConfig(config);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:getHistory', async (event, { limit = 50, status = null }) => {
  try {
    const history = autoDownloadService.getHistory(limit, status);
    return { success: true, data: history };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:getActiveDownloads', async () => {
  try {
    const downloads = autoDownloadService.getActiveDownloads();
    return { success: true, data: downloads };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:startDownload', async (event, { anime, episode, videoUrl }) => {
  try {
    const record = await autoDownloadService.startDownload(anime, episode, videoUrl);
    return { success: true, data: record };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:cancelDownload', async (event, { downloadId }) => {
  try {
    const record = await autoDownloadService.cancelDownload(downloadId);
    return { success: true, data: record };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:deleteDownload', async (event, { downloadId }) => {
  try {
    await autoDownloadService.deleteDownload(downloadId);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:getStatus', async () => {
  try {
    const status = autoDownloadService.getStatus();
    return { success: true, data: status };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:previewFilter', async (event, { animeList }) => {
  try {
    const filtered = autoDownloadService.previewFilter(animeList);
    return { success: true, data: filtered };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:getProgress', async (event, { episodeId }) => {
  try {
    const progress = autoDownloadService._videoDownloader?.getProgress(episodeId);
    return { success: true, data: progress };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:getAllDownloads', async () => {
  try {
    const downloads = autoDownloadService._videoDownloader?.getAllDownloads() || [];
    return { success: true, data: downloads };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('autoDownload:clearCompleted', async () => {
  try {
    autoDownloadService.clearCompletedDownloads();
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// IPC Handlers for Performance
ipcMain.handle('performance:record', async (event, data) => {
  try {
    const service = getPerformanceService();
    const result = await service.recordPerformance(data);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('performance:batchRecord', async (event, items) => {
  try {
    const service = getPerformanceService();
    const results = await service.batchRecordPerformance(items);
    return { success: true, data: results };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('performance:getStats', async () => {
  try {
    const service = getPerformanceService();
    const stats = service.getStats();
    return { success: true, stats };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('performance:getRecentTraces', async (event, options) => {
  try {
    const service = getPerformanceService();
    const { traces, total } = service.getRecentTraces(options);
    return { success: true, traces, total };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('performance:getTrace', async (event, traceId) => {
  try {
    const service = getPerformanceService();
    const trace = service.getTraceChain(traceId);
    return { success: true, ...trace };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('performance:clearAll', async () => {
  try {
    const service = getPerformanceService();
    await service.clearAllData();
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Create window
const createWindow = async () => {
  // Load saved window state
  await loadWindowState();
  
  mainWindow = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    show: false, // Don't show until ready
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
    },
  });

  // Handle response headers: CSP for app + CORS for video
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    const url = details.url;
    const responseHeaders = { ...details.responseHeaders };
    
    // For video requests, add permissive CORS headers
    if (url.includes('.v.anime1.me') || url.includes('.mp4') || url.includes('.m3u8')) {
      // Remove restrictive CORS headers
      delete responseHeaders['access-control-allow-origin'];
      delete responseHeaders['Access-Control-Allow-Origin'];
      delete responseHeaders['access-control-allow-credentials'];
      delete responseHeaders['Access-Control-Allow-Credentials'];
      // Add permissive CORS headers
      responseHeaders['Access-Control-Allow-Origin'] = ['*'];
      responseHeaders['Access-Control-Allow-Credentials'] = ['true'];
      responseHeaders['Access-Control-Allow-Headers'] = ['*'];
    }
    
    // Add CSP headers for all responses
    responseHeaders['Content-Security-Policy'] = [
      "default-src 'self' 'unsafe-inline' data:; " +
      "script-src 'self' 'unsafe-eval'; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data: https: http:; " +
      "connect-src 'self' https: http:; " +
      "media-src 'self' https: http: blob:;"
    ];
    
    callback({ responseHeaders });
  });

  // Add Referer header for video requests
  mainWindow.webContents.session.webRequest.onBeforeSendHeaders((details, callback) => {
    const url = details.url;
    // Add referer for anime1 video requests
    if (url.includes('.v.anime1.me') || url.includes('anime1.me')) {
      details.requestHeaders['Referer'] = 'https://anime1.me/';
      details.requestHeaders['Origin'] = 'https://anime1.me';
    }
    callback({ requestHeaders: details.requestHeaders });
  });

  mainWindow.loadURL(MAIN_WINDOW_WEBPACK_ENTRY);
  
  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (windowState.maximized) {
      mainWindow.maximize();
    }
  });
  
  mainWindow.webContents.openDevTools();
  
  // Listen for console messages from preload/renderer
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Console] ${message}`);
  });

  // Save window state on close
  mainWindow.on('close', async () => {
    await saveWindowState();
  });
  
  // Handle minimize to tray
  mainWindow.on('minimize', (event) => {
    // On Windows/Linux, minimize to tray
    if (process.platform !== 'darwin') {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  // Initialize auto updater
  initUpdater(mainWindow);
  
  // Set WebContents for auto download service to send events
  const autoDownloadService = getAutoDownloadService();
  autoDownloadService.setWebContents(mainWindow.webContents);

  return mainWindow;
};

app.whenReady().then(async () => {
  await initializeApp();
  await createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });
}
