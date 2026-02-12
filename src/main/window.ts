/**
 * 窗口管理模块
 * 
 * 对应原项目: src/desktop.py 中的窗口管理部分
 * 职责: 创建和管理应用窗口、系统托盘、全局快捷键
 */

import { 
  BrowserWindow, 
  Tray, 
  Menu, 
  nativeImage,
  screen,
  ipcMain,
  app
} from 'electron'
import { join } from 'path'
import log from 'electron-log'

// 窗口状态接口
interface WindowState {
  width: number
  height: number
  x?: number
  y?: number
  maximized: boolean
  fullscreen: boolean
}

// 默认窗口配置
const DEFAULT_WINDOW_STATE: WindowState = {
  width: 1280,
  height: 800,
  maximized: false,
  fullscreen: false
}

// 最小窗口尺寸
const MIN_WINDOW_SIZE = {
  width: 900,
  height: 600
}

export class WindowManager {
  private mainWindow: BrowserWindow | null = null
  private tray: Tray | null = null
  private windowState: WindowState = { ...DEFAULT_WINDOW_STATE }

  /**
   * 创建主窗口
   */
  async createMainWindow(): Promise<BrowserWindow> {
    // 加载保存的窗口状态
    this.loadWindowState()

    // 创建窗口
    this.mainWindow = new BrowserWindow({
      width: this.windowState.width,
      height: this.windowState.height,
      x: this.windowState.x,
      y: this.windowState.y,
      minWidth: MIN_WINDOW_SIZE.width,
      minHeight: MIN_WINDOW_SIZE.height,
      title: 'Anime1 Desktop',
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      show: false, // 先不显示，等加载完成
      webPreferences: {
        preload: join(__dirname, '../preload/index.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
        allowRunningInsecureContent: false,
        webSecurity: true
      },
      icon: join(__dirname, '../../../resources/icon.png')
    })

    // 恢复窗口状态
    if (this.windowState.maximized) {
      this.mainWindow.maximize()
    }
    if (this.windowState.fullscreen) {
      this.mainWindow.setFullScreen(true)
    }

    // 加载页面
    if (process.env.VITE_DEV_SERVER_URL) {
      // 开发模式
      await this.mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
      this.mainWindow.webContents.openDevTools()
    } else {
      // 生产模式
      await this.mainWindow.loadFile(join(__dirname, '../../dist/index.html'))
    }

    // 显示窗口
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show()
      log.info('[Window] Main window shown')
    })

    // 窗口事件监听
    this.setupWindowEvents()

    // 创建系统托盘
    this.createTray()

    // 注册 IPC
    this.registerWindowIPC()

    log.info('[Window] Main window created')
    return this.mainWindow
  }

  /**
   * 设置窗口事件
   */
  private setupWindowEvents(): void {
    if (!this.mainWindow) return

    // 保存窗口状态
    this.mainWindow.on('close', () => {
      this.saveWindowState()
    })

    this.mainWindow.on('closed', () => {
      this.mainWindow = null
    })

    // 最大化/恢复
    this.mainWindow.on('maximize', () => {
      this.windowState.maximized = true
    })

    this.mainWindow.on('unmaximize', () => {
      this.windowState.maximized = false
    })

    // 全屏
    this.mainWindow.on('enter-full-screen', () => {
      this.windowState.fullscreen = true
    })

    this.mainWindow.on('leave-full-screen', () => {
      this.windowState.fullscreen = false
    })

    // 处理外部链接
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      // 只允许特定域名
      const allowedDomains = ['anime1.me', 'bgm.tv', 'github.com']
      const urlObj = new URL(url)
      
      if (allowedDomains.some(domain => urlObj.hostname.includes(domain))) {
        return { action: 'allow' }
      }
      
      // 其他链接用系统浏览器打开
      const { shell } = require('electron')
      shell.openExternal(url)
      return { action: 'deny' }
    })
  }

  /**
   * 创建系统托盘
   */
  private createTray(): void {
    // TODO: 创建 tray 图标
    // const iconPath = join(__dirname, '../../../resources/tray-icon.png')
    // const trayIcon = nativeImage.createFromPath(iconPath)
    // this.tray = new Tray(trayIcon)
    
    // const contextMenu = Menu.buildFromTemplate([
    //   { label: '显示窗口', click: () => this.show() },
    //   { label: '退出', click: () => app.quit() }
    // ])
    
    // this.tray.setContextMenu(contextMenu)
    // this.tray.setToolTip('Anime1 Desktop')
    // this.tray.on('click', () => this.show())
  }

  /**
   * 注册窗口相关 IPC
   */
  private registerWindowIPC(): void {
    // 最小化
    ipcMain.handle('window:minimize', () => {
      this.mainWindow?.minimize()
    })

    // 最大化/恢复
    ipcMain.handle('window:maximize', () => {
      if (this.mainWindow?.isMaximized()) {
        this.mainWindow.restore()
      } else {
        this.mainWindow?.maximize()
      }
    })

    // 关闭窗口（最小化到托盘或退出）
    ipcMain.handle('window:close', () => {
      // 默认直接退出，后续可改为最小化到托盘
      this.mainWindow?.close()
    })

    // 全屏切换
    ipcMain.handle('window:toggleFullscreen', () => {
      this.mainWindow?.setFullScreen(!this.mainWindow.isFullScreen())
    })

    // 获取窗口状态
    ipcMain.handle('window:getState', () => {
      return {
        maximized: this.mainWindow?.isMaximized() ?? false,
        minimized: this.mainWindow?.isMinimized() ?? false,
        fullscreen: this.mainWindow?.isFullScreen() ?? false,
        focused: this.mainWindow?.isFocused() ?? false
      }
    })
  }

  /**
   * 加载窗口状态
   */
  private loadWindowState(): void {
    // TODO: 从 electron-store 加载
    // const store = new Store<{ windowState: WindowState }>()
    // this.windowState = store.get('windowState', DEFAULT_WINDOW_STATE)
    
    // 确保窗口在屏幕范围内
    if (this.windowState.x !== undefined && this.windowState.y !== undefined) {
      const displays = screen.getAllDisplays()
      const isInBounds = displays.some(display => {
        const { x, y, width, height } = display.bounds
        return (
          this.windowState.x! >= x &&
          this.windowState.x! <= x + width &&
          this.windowState.y! >= y &&
          this.windowState.y! <= y + height
        )
      })
      
      if (!isInBounds) {
        this.windowState.x = undefined
        this.windowState.y = undefined
      }
    }
  }

  /**
   * 保存窗口状态
   */
  private saveWindowState(): void {
    if (!this.mainWindow) return

    const bounds = this.mainWindow.getBounds()
    this.windowState = {
      ...this.windowState,
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y
    }

    // TODO: 保存到 electron-store
    // const store = new Store<{ windowState: WindowState }>()
    // store.set('windowState', this.windowState)
  }

  /**
   * 显示窗口
   */
  show(): void {
    if (this.mainWindow) {
      if (this.mainWindow.isMinimized()) {
        this.mainWindow.restore()
      }
      this.mainWindow.show()
      this.mainWindow.focus()
    }
  }

  /**
   * 隐藏窗口
   */
  hide(): void {
    this.mainWindow?.hide()
  }

  /**
   * 聚焦窗口
   */
  focus(): void {
    this.show()
  }

  /**
   * 获取主窗口
   */
  getMainWindow(): BrowserWindow | null {
    return this.mainWindow
  }
}
