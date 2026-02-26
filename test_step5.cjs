const { app, BrowserWindow } = require('electron');
const log = require('electron-log');  // 新增: 导入 electron-log

class WindowManager {
  constructor() {
    this.mainWindow = null;
  }
  
  async createMainWindow() {
    const preloadPath = '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs';
    console.log('[WM] Step 5: With electron-log import');
    
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

app.whenReady().then(async () => {
  const wm = new WindowManager();
  await wm.createMainWindow();
});
