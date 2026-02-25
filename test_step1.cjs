// 步骤 1: 最基本的 WindowManager
const { app, BrowserWindow } = require('electron');

class WindowManager {
  constructor() {
    this.mainWindow = null;
  }
  
  async createMainWindow() {
    const preloadPath = '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs';
    console.log('[WM] Creating window with preload:', preloadPath);
    
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false
      }
    });
    
    this.mainWindow.loadURL('http://localhost:5173/');
    
    this.mainWindow.webContents.on('console-message', (e) => {
      console.log('[Console]', e.message);
    });
  }
}

app.whenReady().then(async () => {
  const wm = new WindowManager();
  await wm.createMainWindow();
});
