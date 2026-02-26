/**
 * Anime1 Desktop - Electron Main Process
 * 
 * 对应原项目: src/desktop.py + src/app.py
 * 职责: 应用程序入口、窗口管理、服务初始化
 */

import { app, BrowserWindow, shell, nativeImage } from 'electron'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import log from 'electron-log'

// 获取 __dirname 等效（ES 模块）
const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// 设置应用名称（必须在应用ready之前）
app.setName('Anime1 Desktop')

// 设置 Dock 图标（macOS）
if (process.platform === 'darwin') {
  const iconPath = join(__dirname, '../../../resources/icon.png')
  try {
    const dockIcon = nativeImage.createFromPath(iconPath)
    app.dock.setIcon(dockIcon)
    console.log('[Main] Dock icon set successfully')
  } catch (error) {
    console.error('[Main] Failed to set dock icon:', error)
  }
}

// 启用远程调试（开发模式）
if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
  app.commandLine.appendSwitch('remote-debugging-port', '9222')
  app.commandLine.appendSwitch('remote-allow-origins', '*')
}

// 服务导入
import { WindowManager } from './window'
import { registerIPCHandlers } from './ipc'
import { DatabaseService } from './services/database'
import { AnimeService } from './services/anime'
import { CrawlerService } from './services/crawler'
import { DownloadService } from './services/download'
import { UpdateService } from './services/update'
import { AutoDownloadService } from './services/autoDownload'
import { videoProxyService } from './services/video-proxy'

// 配置
const APP_NAME = 'Anime1 Desktop'
const APP_VERSION = '2.0.0'

// 全局服务实例
let windowManager: WindowManager | null = null
let databaseService: DatabaseService | null = null
let animeService: AnimeService | null = null
let crawlerService: CrawlerService | null = null
let downloadService: DownloadService | null = null
let updateService: UpdateService | null = null
let autoDownloadService: AutoDownloadService | null = null

// 日志配置
// 处理 EPIPE 错误：当 npm run dev 的管道关闭时，忽略写入错误
process.stdout.on('error', (err: NodeJS.ErrnoException) => {
  if (err.code === 'EPIPE') {
    // 忽略 EPIPE 错误，这是 npm run dev 的正常行为
    return
  }
  console.error('stdout error:', err)
})

process.stderr.on('error', (err: NodeJS.ErrnoException) => {
  if (err.code === 'EPIPE') {
    // 忽略 EPIPE 错误
    return
  }
  console.error('stderr error:', err)
})

log.initialize({ preload: false })
log.transports.file.level = 'info'
// 开发模式下 console 日志级别设为 info，避免过多调试日志
log.transports.console.level = process.env.NODE_ENV === 'development' ? 'info' : 'debug'
console.log('[Main] Log initialized')

/**
 * 初始化服务
 */
async function initializeServices(): Promise<void> {
  log.info('[Main] Initializing services...')
  
  // 1. 数据库服务（最先初始化）
  databaseService = new DatabaseService()
  await databaseService.connect()
  log.info('[Main] Database service initialized')
  
  // 2. 爬虫服务
  crawlerService = new CrawlerService()
  log.info('[Main] Crawler service initialized')
  
  // 3. 番剧服务
  animeService = new AnimeService(databaseService, crawlerService)
  await animeService.initialize()
  log.info('[Main] Anime service initialized')
  
  // 4. 下载服务
  downloadService = new DownloadService()
  log.info('[Main] Download service initialized')
  
  // 5. 更新服务
  updateService = new UpdateService()
  log.info('[Main] Update service initialized')
  
  // 6. 自动下载服务
  autoDownloadService = new AutoDownloadService()
  autoDownloadService.startScheduler()
  log.info('[Main] Auto download service initialized')
  
  // 注册 IPC 处理器
  registerIPCHandlers({
    databaseService,
    animeService,
    crawlerService,
    downloadService,
    updateService,
    autoDownloadService
  })
  log.info('[Main] IPC handlers registered')
}

/**
 * 创建窗口
 */
async function createWindow(): Promise<void> {
  windowManager = new WindowManager()
  await windowManager.createMainWindow()
  log.info('[Main] Main window created')
}

/**
 * 应用就绪
 */
app.whenReady().then(async () => {
  log.info(`[Main] ${APP_NAME} v${APP_VERSION} starting...`)
  
  try {
    // 初始化视频代理协议（必须在 app.ready 后）
    videoProxyService.initialize()
    
    // 初始化服务
    await initializeServices()
    
    // 创建窗口
    await createWindow()
    
    log.info('[Main] Application ready')
    
    // macOS: 点击 dock 图标重新创建窗口
    app.on('activate', async () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        await createWindow()
      }
    })
    
    // 检查更新
    if (updateService) {
      await updateService.checkForUpdates()
    }
  } catch (error) {
    log.error('[Main] Failed to initialize:', error)
    app.quit()
  }
})

/**
 * 所有窗口关闭
 */
app.on('window-all-closed', () => {
  log.info('[Main] All windows closed')
  
  // macOS: 保持应用运行
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

/**
 * 应用退出前
 */
app.on('before-quit', async () => {
  log.info('[Main] Application quitting...')
  
  // 设置退出标志
  windowManager?.setQuitting(true)
  
  // 清理资源
  if (downloadService) {
    await downloadService.pauseAll()
  }
  
  if (databaseService) {
    databaseService.close()
  }
  
  log.info('[Main] Cleanup complete')
})

/**
 * 安全策略：阻止新窗口创建
 */
app.on('web-contents-created', (_, contents) => {
  contents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })
})

/**
 * 单实例锁（测试模式下禁用）
 */
if (!process.env.E2E_TEST) {
  const gotTheLock = app.requestSingleInstanceLock()

  if (!gotTheLock) {
    log.warn('[Main] Another instance is already running')
    app.quit()
  } else {
    app.on('second-instance', () => {
      // 用户尝试打开第二个实例时，显示并聚焦窗口
      if (windowManager) {
        windowManager.show()
      }
    })
  }
}
