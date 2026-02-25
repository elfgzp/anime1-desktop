const { app, BrowserWindow } = require('electron');

app.whenReady().then(() => {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: '/Users/gzp/Github/anime1-desktop-electron/dist-electron/preload/index.cjs',
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  
  win.loadURL('http://localhost:5173/');
  
  win.webContents.on('console-message', (e) => {
    console.log('Console:', e.message);
  });
});
