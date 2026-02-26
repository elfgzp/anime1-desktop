const { app, BrowserWindow } = require('electron');

app.whenReady().then(() => {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Anime1 Desktop',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    show: false,  // 与主应用相同
    webPreferences: {
      preload: '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs',
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      allowRunningInsecureContent: true  // 与主应用相同
    }
  });
  
  win.loadURL('http://localhost:5173/');
  
  win.once('ready-to-show', () => {
    win.show();
  });
  
  win.webContents.on('console-message', (e) => {
    console.log('Console:', e.message);
  });
});
