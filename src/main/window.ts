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
  globalShortcut,
  shell
} from 'electron'
import { join, dirname, resolve } from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'
import log from 'electron-log'
import { config, WINDOW_CONFIG } from './config'

// ES 模块中的 __dirname polyfill - 使用绝对路径
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

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
  private normalBounds: { width: number; height: number; x: number; y: number } | null = null

  /**
   * 创建主窗口
   */
  async createMainWindow(): Promise<BrowserWindow> {
    // 加载保存的窗口状态
    const windowState = this.loadWindowState()

    // 计算 preload 路径 - 使用相对路径
    const preloadPath = join(__dirname, '../preload/index.cjs')
    const absolutePreloadPath = resolve(preloadPath)
    console.log(`[Window] Preload path: ${preloadPath}`)
    console.log(`[Window] Preload absolute path: ${absolutePreloadPath}`)
    console.log(`[Window] Preload exists: ${existsSync(preloadPath)}`)
    
    // 验证 preload 文件可读
    try {
      const { readFileSync } = await import('fs')
      const content = readFileSync(preloadPath, 'utf8')
      console.log(`[Window] Preload file size: ${content.length} bytes`)
    } catch (e: any) {
      console.error(`[Window] Preload file read error: ${e.message}`)
    }
    
    // 创建窗口（无边框，使用自定义标题栏）
    this.mainWindow = new BrowserWindow({
      width: windowState.width,
      height: windowState.height,
      x: windowState.x,
      y: windowState.y,
      minWidth: WINDOW_CONFIG.MIN_WIDTH,
      minHeight: WINDOW_CONFIG.MIN_HEIGHT,
      title: 'Anime1 Desktop',
      frame: false, // 无边框窗口
      show: false,
      webPreferences: {
        preload: preloadPath,
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false,
        allowRunningInsecureContent: true
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
      // 开发模式：使用 Vite dev server
      log.info(`[Window] Loading dev server: ${process.env.VITE_DEV_SERVER_URL}`)
      await this.mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    } else {
      // 生产模式：使用构建后的文件
      const indexPath = join(__dirname, '../../dist/index.html')
      log.info(`[Window] Loading production build: ${indexPath}`)
      await this.mainWindow.loadFile(indexPath)
    }
    this.mainWindow.webContents.openDevTools()

    // 显示窗口 - 使用 setTimeout 确保即使 ready-to-show 不触发也能显示
    const showWindow = () => {
      if (this.mainWindow && !this.mainWindow.isVisible()) {
        this.mainWindow.show()
        log.info('[Window] Main window shown')
      }
    }
    
    // 方法1: ready-to-show 事件
    this.mainWindow.once('ready-to-show', showWindow)
    
    // 方法2: 3秒后强制显示（防止 ready-to-show 不触发）
    setTimeout(showWindow, 3000)
    
    // 方法3: did-finish-load 事件
    this.mainWindow.webContents.once('did-finish-load', showWindow)

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

    // 监听 preload 错误
    this.mainWindow.webContents.on('preload-error', (event, preloadPath, error) => {
      log.error('[Window] Preload error:', preloadPath, error)
    })
    
    // 监听 console-message (Electron 40+ 新 API)
    this.mainWindow.webContents.on('console-message', (event: any) => {
      const message = event.message || ''
      log.info('[Window] Console:', message)
      if (message.includes('[Preload]')) {
        log.info('[Window] Preload console:', message)
      }
    })

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

    // 最大化/恢复（使用自定义实现，适配无边框窗口）
    ipcMain.handle('window:maximize', () => {
      const win = this.mainWindow
      if (!win) return { success: false, maximized: false }
      
      // 检查是否已经是最大化状态（通过比较窗口大小和屏幕大小）
      const bounds = win.getBounds()
      const screenBounds = screen.getPrimaryDisplay().workAreaSize
      const isMaximized = bounds.width >= screenBounds.width && bounds.height >= screenBounds.height
      
      log.info(`[Window] Maximize toggled, current size: ${bounds.width}x${bounds.height}, screen: ${screenBounds.width}x${screenBounds.height}`)
      
      if (isMaximized) {
        // 恢复之前的大小
        if (this.normalBounds) {
          win.setBounds(this.normalBounds)
          log.info('[Window] Window restored to:', this.normalBounds)
        } else {
          // 使用默认大小
          const defaultSize = { width: WINDOW_CONFIG.DEFAULT_WIDTH, height: WINDOW_CONFIG.DEFAULT_HEIGHT }
          win.setSize(defaultSize.width, defaultSize.height)
          win.center()
          log.info('[Window] Window restored to default size')
        }
      } else {
        // 保存当前大小和位置，然后最大化
        this.normalBounds = { ...bounds }
        win.setBounds({
          x: 0,
          y: 0,
          width: screenBounds.width,
          height: screenBounds.height
        })
        log.info('[Window] Window maximized')
      }
      
      return { success: true, maximized: !isMaximized }
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
      const state = {
        maximized: this.mainWindow?.isMaximized() ?? false,
        minimized: this.mainWindow?.isMinimized() ?? false,
        fullscreen: this.mainWindow?.isFullScreen() ?? false,
        focused: this.mainWindow?.isFocused() ?? false
      }
      log.info('[Window] getState called:', state)
      return state
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
