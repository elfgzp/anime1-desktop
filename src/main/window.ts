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
  app,
  globalShortcut
} from 'electron'
import { join } from 'path'
import log from 'electron-log'
import { config, WINDOW_CONFIG } from './config'

// 窗口状态接口
interface WindowState {
  width: number
  height: number
  x?: number
  y?: number
  maximized: boolean
  fullscreen: boolean
}

// 默认窗口状态
const DEFAULT_WINDOW_STATE: WindowState = {
  width: WINDOW_CONFIG.DEFAULT_WIDTH,
  height: WINDOW_CONFIG.DEFAULT_HEIGHT,
  maximized: false,
  fullscreen: false
}

export class WindowManager {
  private mainWindow: BrowserWindow | null = null
  private tray: Tray | null = null
  private isQuitting = false

  /**
   * 创建主窗口
   */
  async createMainWindow(): Promise<BrowserWindow> {
    // 加载保存的窗口状态
    const windowState = this.loadWindowState()

    // 创建窗口
    this.mainWindow = new BrowserWindow({
      width: windowState.width,
      height: windowState.height,
      x: windowState.x,
      y: windowState.y,
      minWidth: WINDOW_CONFIG.MIN_WIDTH,
      minHeight: WINDOW_CONFIG.MIN_HEIGHT,
      title: 'Anime1 Desktop',
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
      show: false,
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
    if (windowState.maximized) {
      this.mainWindow.maximize()
    }
    if (windowState.fullscreen) {
      this.mainWindow.setFullScreen(true)
    }

    // 加载页面
    if (process.env.VITE_DEV_SERVER_URL) {
      await this.mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
      this.mainWindow.webContents.openDevTools()
    } else {
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

    // 注册全局快捷键
    this.registerGlobalShortcuts()

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
    const saveState = () => {
      this.saveWindowState()
    }

    this.mainWindow.on('resize', saveState)
    this.mainWindow.on('move', saveState)
    this.mainWindow.on('maximize', saveState)
    this.mainWindow.on('unmaximize', saveState)
    this.mainWindow.on('enter-full-screen', saveState)
    this.mainWindow.on('leave-full-screen', saveState)

    // 关闭处理
    this.mainWindow.on('close', (event) => {
      if (!this.isQuitting && process.platform === 'darwin') {
        event.preventDefault()
        this.hide()
      } else {
        saveState()
      }
    })

    this.mainWindow.on('closed', () => {
      this.mainWindow = null
    })

    // 处理外部链接
    this.mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      const allowedDomains = ['anime1.me', 'bgm.tv', 'github.com']
      const urlObj = new URL(url)
      
      if (allowedDomains.some(domain => urlObj.hostname.includes(domain))) {
        return { action: 'allow' }
      }
      
      const { shell } = require('electron')
      shell.openExternal(url)
      return { action: 'deny' }
    })
  }

  /**
   * 创建系统托盘
   */
  private createTray(): void {
    try {
      // 使用原生图标创建 tray
      const iconPath = join(__dirname, '../../../resources/icon.png')
      const trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 })
      
      this.tray = new Tray(trayIcon)
      this.tray.setToolTip('Anime1 Desktop')

      const contextMenu = Menu.buildFromTemplate([
        {
          label: '显示窗口',
          click: () => this.show()
        },
        { type: 'separator' },
        {
          label: '退出',
          click: () => {
            this.isQuitting = true
            app.quit()
          }
        }
      ])

      this.tray.setContextMenu(contextMenu)
      
      // 点击托盘图标显示/隐藏窗口
      this.tray.on('click', () => {
        if (this.mainWindow?.isVisible()) {
          this.hide()
        } else {
          this.show()
        }
      })

      log.info('[Window] Tray created')
    } catch (error) {
      log.warn('[Window] Failed to create tray:', error)
    }
  }

  /**
   * 注册全局快捷键
   */
  private registerGlobalShortcuts(): void {
    // Cmd/Ctrl + Shift + D: 显示/隐藏窗口
    globalShortcut.register('CommandOrControl+Shift+D', () => {
      if (this.mainWindow?.isVisible()) {
        this.hide()
      } else {
        this.show()
      }
    })

    log.info('[Window] Global shortcuts registered')
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

    // 关闭窗口
    ipcMain.handle('window:close', () => {
      this.hide()
    })

    // 全屏切换
    ipcMain.handle('window:toggleFullscreen', () => {
      this.mainWindow?.setFullScreen(!this.mainWindow?.isFullScreen())
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
  private loadWindowState(): WindowState {
    const saved = config.window
    const state = { ...DEFAULT_WINDOW_STATE, ...saved }

    // 确保窗口在屏幕范围内
    if (state.x !== undefined && state.y !== undefined) {
      const displays = screen.getAllDisplays()
      const isInBounds = displays.some(display => {
        const { x, y, width, height } = display.bounds
        return (
          state.x! >= x &&
          state.x! <= x + width &&
          state.y! >= y &&
          state.y! <= y + height
        )
      })
      
      if (!isInBounds) {
        state.x = undefined
        state.y = undefined
      }
    }

    return state
  }

  /**
   * 保存窗口状态
   */
  private saveWindowState(): void {
    if (!this.mainWindow) return

    const bounds = this.mainWindow.getBounds()
    const state: WindowState = {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y,
      maximized: this.mainWindow.isMaximized(),
      fullscreen: this.mainWindow.isFullScreen()
    }

    config.window = state
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

  /**
   * 设置退出标志
   */
  setQuitting(quitting: boolean): void {
    this.isQuitting = quitting
  }
}
