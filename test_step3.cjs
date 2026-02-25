const { app, BrowserWindow } = require('electron');

class WindowManager {
  constructor() {
    this.mainWindow = null;
  }
  
  async createMainWindow() {
    const preloadPath = '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs';
    console.log('[WM] Step 3: Adding titleBarStyle and allowRunningInsecureContent');
    
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      title: 'Anime1 Desktop',
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',  // 新增
      show: false,
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false,
        allowRunningInsecureContent: true  // 新增
      }
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
