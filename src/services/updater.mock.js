/**
 * Mock Auto Updater Service for Testing
 * 
 * 用于测试自动更新功能，无需真实发布到 GitHub Releases
 * 支持模拟各种场景：检查更新、下载进度、错误等
 * 
 * 使用方法:
 * 1. 设置环境变量: MOCK_UPDATER=true
 * 2. 通过 IPC 命令控制 mock 行为
 * 3. 观察 UI 响应
 */

import { ipcMain, BrowserWindow } from 'electron';
import logger from 'electron-log';

// Mock 配置
const MOCK_CONFIG = {
  // 模拟延迟 (ms)
  checkDelay: 2000,
  downloadDelay: 5000,
  progressInterval: 500,
  
  // 默认模拟场景
  scenario: process.env.MOCK_UPDATER_SCENARIO || 'has-update',
  
  // 模拟版本号
  mockVersion: process.env.MOCK_UPDATER_VERSION || '9.9.9',
  
  // 当前应用版本
  currentVersion: process.env.MOCK_CURRENT_VERSION || '1.0.0',
};

// 模拟场景定义
const SCENARIOS = {
  // 场景 1: 无可用更新
  'no-update': {
    hasUpdate: false,
    error: null,
  },
  
  // 场景 2: 有可用更新
  'has-update': {
    hasUpdate: true,
    error: null,
    version: MOCK_CONFIG.mockVersion,
    releaseNotes: '## v9.9.9 更新内容\n\n- ✨ 新增功能：自动下载\n- 🐛 修复视频播放问题\n- ⚡ 性能优化\n- 🔒 安全性提升',
    releaseDate: new Date().toISOString(),
    downloadSize: 1024 * 1024 * 85, // 85 MB
  },
  
  // 场景 3: 检查更新时出错
  'check-error': {
    hasUpdate: false,
    error: {
      message: '无法连接到更新服务器，请检查网络连接',
      code: 'NETWORK_ERROR',
    },
  },
  
  // 场景 4: 下载时出错
  'download-error': {
    hasUpdate: true,
    error: {
      message: '下载更新失败：磁盘空间不足',
      code: 'DISK_FULL',
    },
    downloadFailAt: 50, // 在 50% 时失败
  },
  
  // 场景 5: 已下载等待安装
  'downloaded': {
    hasUpdate: true,
    alreadyDownloaded: true,
    version: MOCK_CONFIG.mockVersion,
  },
};

// 状态管理
let mockState = {
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

let mainWindow = null;
let progressTimer = null;

/**
 * 发送状态到渲染进程
 */
function sendStatusToWindow(channel, data = {}) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('updater:' + channel, data);
  }
}

/**
 * 重置状态
 */
function resetState() {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  
  mockState = {
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
 * 模拟检查更新
 */
async function mockCheckForUpdates() {
  const scenario = SCENARIOS[MOCK_CONFIG.scenario] || SCENARIOS['has-update'];
  
  // 发送 checking 事件
  mockState.checking = true;
  sendStatusToWindow('checking');
  logger.info('[MockUpdater] Checking for update (scenario: ' + MOCK_CONFIG.scenario + ')...');
  
  // 模拟网络延迟
  await delay(MOCK_CONFIG.checkDelay);
  
  // 处理错误场景
  if (scenario.error && !scenario.hasUpdate) {
    mockState.checking = false;
    mockState.error = scenario.error.message;
    sendStatusToWindow('error', { message: scenario.error.message });
    logger.error('[MockUpdater] Check failed:', scenario.error.message);
    
    throw new Error(scenario.error.message);
  }
  
  // 无更新场景
  if (!scenario.hasUpdate) {
    mockState.checking = false;
    sendStatusToWindow('not-available', { version: MOCK_CONFIG.currentVersion });
    logger.info('[MockUpdater] Update not available');
    
    return {
      updateInfo: {
        version: MOCK_CONFIG.currentVersion,
      },
    };
  }
  
  // 有更新场景
  mockState.checking = false;
  mockState.available = true;
  mockState.info = {
    version: scenario.version,
    releaseDate: scenario.releaseDate,
    releaseNotes: scenario.releaseNotes,
  };
  
  sendStatusToWindow('available', mockState.info);
  logger.info('[MockUpdater] Update available:', scenario.version);
  
  // 如果配置为自动下载
  if (mockState.downloaded || scenario.alreadyDownloaded) {
    mockState.downloaded = true;
    mockState.progress.percent = 100;
    sendStatusToWindow('downloaded', mockState.info);
  }
  
  return {
    updateInfo: {
      version: scenario.version,
      releaseDate: scenario.releaseDate,
      releaseNotes: scenario.releaseNotes,
      files: [{
        url: `https://github.com/gzp/anime1-desktop/releases/download/v${scenario.version}/Anime1Desktop-${scenario.version}.dmg`,
        size: scenario.downloadSize || 0,
      }],
    },
  };
}

/**
 * 模拟下载更新
 */
async function mockDownloadUpdate() {
  const scenario = SCENARIOS[MOCK_CONFIG.scenario] || SCENARIOS['has-update'];
  
  if (!mockState.available) {
    throw new Error('No update available');
  }
  
  // 如果已下载
  if (mockState.downloaded || scenario.alreadyDownloaded) {
    logger.info('[MockUpdater] Update already downloaded');
    return Promise.resolve();
  }
  
  mockState.downloading = true;
  const totalSize = scenario.downloadSize || 1024 * 1024 * 50; // 默认 50MB
  
  // 模拟下载进度
  return new Promise((resolve, reject) => {
    let progress = 0;
    const increment = 100 / (MOCK_CONFIG.downloadDelay / MOCK_CONFIG.progressInterval);
    
    progressTimer = setInterval(() => {
      progress += increment;
      
      // 处理下载错误场景
      if (scenario.error && scenario.downloadFailAt && progress >= scenario.downloadFailAt) {
        clearInterval(progressTimer);
        mockState.downloading = false;
        mockState.error = scenario.error.message;
        sendStatusToWindow('error', { message: scenario.error.message });
        logger.error('[MockUpdater] Download failed:', scenario.error.message);
        reject(new Error(scenario.error.message));
        return;
      }
      
      // 正常进度
      if (progress >= 100) {
        progress = 100;
        clearInterval(progressTimer);
        
        mockState.downloading = false;
        mockState.downloaded = true;
        mockState.progress = {
          percent: 100,
          bytesPerSecond: 0,
          total: totalSize,
          transferred: totalSize,
        };
        
        sendStatusToWindow('downloaded', mockState.info);
        logger.info('[MockUpdater] Update downloaded');
        resolve();
      } else {
        // 发送进度
        const transferred = Math.floor(totalSize * (progress / 100));
        mockState.progress = {
          percent: Math.round(progress),
          bytesPerSecond: 1024 * 1024 * 2, // 模拟 2MB/s
          total: totalSize,
          transferred: transferred,
        };
        
        sendStatusToWindow('progress', mockState.progress);
        logger.debug('[MockUpdater] Download progress:', Math.round(progress) + '%');
      }
    }, MOCK_CONFIG.progressInterval);
  });
}

/**
 * 模拟安装更新
 */
function mockQuitAndInstall() {
  logger.info('[MockUpdater] Quit and install (mock)');
  
  // 模拟安装延迟
  sendStatusToWindow('installing');
  
  setTimeout(() => {
    logger.info('[MockUpdater] Would restart app now');
    // 在真实环境中这里会重启应用
    // 在 mock 模式下我们只是记录日志
  }, 1000);
}

/**
 * 辅助函数：延迟
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 格式化字节
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 设置 IPC 处理器
 */
function setupIpcHandlers() {
  // 检查更新
  ipcMain.handle('updater:check', async () => {
    try {
      resetState();
      const result = await mockCheckForUpdates();
      
      const scenario = SCENARIOS[MOCK_CONFIG.scenario] || SCENARIOS['has-update'];
      
      if (!result.updateInfo || result.updateInfo.version === MOCK_CONFIG.currentVersion) {
        return {
          success: true,
          data: {
            has_update: false,
            current_version: MOCK_CONFIG.currentVersion,
            latest_version: result.updateInfo?.version || MOCK_CONFIG.currentVersion,
          }
        };
      }
      
      return {
        success: true,
        data: {
          has_update: true,
          current_version: MOCK_CONFIG.currentVersion,
          latest_version: result.updateInfo.version,
          is_prerelease: false,
          release_notes: result.updateInfo.releaseNotes || '',
          download_url: `https://github.com/gzp/anime1-desktop/releases/tag/v${result.updateInfo.version}`,
          asset_name: `Anime1Desktop-${result.updateInfo.version}-Setup.exe`,
          download_size: formatBytes(scenario.downloadSize || 0),
          published_at: result.updateInfo.releaseDate || new Date().toISOString(),
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        error_type: 'update_check_failed',
        data: {
          has_update: false,
          current_version: MOCK_CONFIG.currentVersion,
          latest_version: null,
        }
      };
    }
  });

  // 下载更新
  ipcMain.handle('updater:download', async () => {
    try {
      if (!mockState.available) {
        return {
          success: false,
          error: 'No update available',
        };
      }

      await mockDownloadUpdate();
      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  });

  // 安装更新
  ipcMain.handle('updater:install', () => {
    try {
      if (!mockState.downloaded) {
        return {
          success: false,
          error: 'Update not downloaded yet',
        };
      }

      mockQuitAndInstall();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  });

  // 获取当前状态
  ipcMain.handle('updater:status', () => {
    return {
      success: true,
      data: mockState,
    };
  });
  
  // ===== Mock 专用 IPC 命令 =====
  
  // 切换场景
  ipcMain.handle('mock-updater:set-scenario', (event, scenario) => {
    if (SCENARIOS[scenario]) {
      MOCK_CONFIG.scenario = scenario;
      resetState();
      logger.info('[MockUpdater] Scenario changed to:', scenario);
      return { success: true, scenario };
    }
    return { success: false, error: 'Unknown scenario' };
  });
  
  // 获取可用场景列表
  ipcMain.handle('mock-updater:get-scenarios', () => {
    return {
      success: true,
      data: Object.keys(SCENARIOS).map(key => ({
        id: key,
        name: getScenarioName(key),
        description: getScenarioDescription(key),
      })),
    };
  });
  
  // 获取当前配置
  ipcMain.handle('mock-updater:get-config', () => {
    return {
      success: true,
      data: {
        ...MOCK_CONFIG,
        isMock: true,
      },
    };
  });
  
  // 手动触发事件
  ipcMain.handle('mock-updater:trigger-event', (event, { eventName, data }) => {
    sendStatusToWindow(eventName, data);
    return { success: true };
  });
  
  // 重置状态
  ipcMain.handle('mock-updater:reset', () => {
    resetState();
    return { success: true, state: mockState };
  });
}

/**
 * 获取场景名称
 */
function getScenarioName(key) {
  const names = {
    'no-update': '无更新',
    'has-update': '有可用更新',
    'check-error': '检查更新失败',
    'download-error': '下载失败',
    'downloaded': '已下载等待安装',
  };
  return names[key] || key;
}

/**
 * 获取场景描述
 */
function getScenarioDescription(key) {
  const descriptions = {
    'no-update': '模拟最新版本，无可用更新',
    'has-update': '模拟发现新版本 v9.9.9，可测试完整更新流程',
    'check-error': '模拟网络错误，检查更新时失败',
    'download-error': '模拟下载到 50% 时失败',
    'downloaded': '模拟更新已下载完成，等待安装',
  };
  return descriptions[key] || '';
}

/**
 * 初始化 Mock Updater
 */
export function initMockUpdater(win) {
  mainWindow = win;
  setupIpcHandlers();
  
  logger.info('[MockUpdater] Initialized');
  logger.info('[MockUpdater] Current scenario:', MOCK_CONFIG.scenario);
  logger.info('[MockUpdater] Mock version:', MOCK_CONFIG.mockVersion);
  
  return {
    isMock: true,
    scenario: MOCK_CONFIG.scenario,
  };
}

/**
 * 获取当前状态
 */
export function getMockState() {
  return { ...mockState };
}

/**
 * 获取可用场景
 */
export function getAvailableScenarios() {
  return Object.keys(SCENARIOS);
}

/**
 * 切换场景
 */
export function setScenario(scenario) {
  if (SCENARIOS[scenario]) {
    MOCK_CONFIG.scenario = scenario;
    resetState();
    return true;
  }
  return false;
}

export default {
  initMockUpdater,
  getMockState,
  getAvailableScenarios,
  setScenario,
};
