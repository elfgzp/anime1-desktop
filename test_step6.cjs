const { app, BrowserWindow, ipcMain } = require('electron');
const log = require('electron-log');

// 模拟主应用的 initializeServices
async function initializeServices() {
  console.log('[Main] Initializing services...');
  
  // 注册一些 IPC handlers（模拟）
  ipcMain.handle('anime:list', () => ({ success: true, data: [] }));
  ipcMain.handle('favorite:list', () => ({ success: true, data: [] }));
  ipcMain.handle('update:check', () => ({ success: true }));
  
  console.log('[Main] Services initialized');
}

class WindowManager {
  constructor() {
    this.mainWindow = null;
  }
  
  async createMainWindow() {
    const preloadPath = '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs';
    console.log('[WM] Step 6: Full main process simulation');
    
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      title: 'Anime1 Desktop',
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      show: false,
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false,
        allowRunningInsecureContent: true
      }
    });
    
    this.mainWindow.webContents.openDevTools();
    
    this.mainWindow.webContents.on('preload-error', (event, preloadPath, error) => {
      console.error('[WM] Preload error:', preloadPath, error);
    });
    
    this.mainWindow.loadURL('http://localhost:5173/');
    
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      console.log('[WM] Window shown');
    });
    
    this.mainWindow.webContents.on('console-message', (e) => {
      console.log('[Console]', e.message);
    });
  }
}

// 模拟主应用的 app.whenReady
app.whenReady().then(async () => {
  console.log('[Main] App starting...');
  
  try {
    await initializeServices();
    
    const wm = new WindowManager();
    await wm.createMainWindow();
    
    console.log('[Main] App ready');
  } catch (error) {
    console.error('[Main] Failed:', error);
  }
});
