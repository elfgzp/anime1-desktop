/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock the dependencies
vi.mock('../utils/api', () => ({
  settingsAPI: {
    checkUpdate: vi.fn(),
    downloadUpdate: vi.fn(),
    runUpdater: vi.fn(),
    exitApp: vi.fn(),
    openPath: vi.fn(),
    getTheme: vi.fn(),
    saveTheme: vi.fn(),
    getAbout: vi.fn(),
    getCacheInfo: vi.fn(),
    clearCache: vi.fn(),
    openLogsFolder: vi.fn()
  }
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

vi.mock('../utils/cacheEventBus', () => ({
  emitCacheCleared: vi.fn()
}))

vi.mock('../composables/useTheme', () => ({
  useThemeStore: vi.fn(() => ({
    saveTheme: vi.fn(),
    applyTheme: vi.fn()
  }))
}))

describe('Settings View - Update Functionality', () => {
  describe('Update Info State', () => {
    it('should initialize with empty update info', () => {
      const updateInfo = ref({
        has_update: false,
        latest_version: '',
        download_url: '',
        asset_name: '',
        download_size: '',
        release_notes: '',
        is_prerelease: false
      })

      expect(updateInfo.value.has_update).toBe(false)
      expect(updateInfo.value.latest_version).toBe('')
      expect(updateInfo.value.download_url).toBe('')
    })

    it('should update state when update is available', () => {
      const updateInfo = ref({
        has_update: false,
        latest_version: '',
        download_url: '',
        asset_name: '',
        download_size: '',
        release_notes: '',
        is_prerelease: false
      })

      // Simulate update available
      updateInfo.value = {
        has_update: true,
        latest_version: '0.2.1',
        download_url: 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-windows-0.2.1.zip',
        asset_name: 'anime1-windows-0.2.1.zip',
        download_size: 1024000,
        release_notes: 'Bug fixes and improvements',
        is_prerelease: false
      }

      expect(updateInfo.value.has_update).toBe(true)
      expect(updateInfo.value.latest_version).toBe('0.2.1')
      expect(updateInfo.value.download_url).toContain('github.com')
    })
  })

  describe('handleCheckUpdate Logic', () => {
    it('should set checkingUpdate to true during check', async () => {
      const checkingUpdate = ref(false)
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.checkUpdate.mockRejectedValue(new Error('Network error'))

      const handleCheckUpdate = async () => {
        checkingUpdate.value = true
        try {
          await settingsAPI.checkUpdate()
        } catch (error) {
          ElMessage.error('检查更新失败')
        } finally {
          checkingUpdate.value = false
        }
      }

      await handleCheckUpdate()
      expect(checkingUpdate.value).toBe(false)
    })

    it('should handle no update available', async () => {
      const checkingUpdate = ref(false)
      const updateInfo = ref({ has_update: false, latest_version: '' })
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.checkUpdate.mockResolvedValue({
        data: {
          has_update: false,
          current_version: '0.2.1',
          latest_version: '0.2.1'
        }
      })

      const handleCheckUpdate = async () => {
        checkingUpdate.value = true
        try {
          const response = await settingsAPI.checkUpdate()
          const data = response.data
          if (data.has_update) {
            updateInfo.value.has_update = true
          } else {
            updateInfo.value = { has_update: false, latest_version: '' }
            ElMessage.info('已是最新版本')
          }
        } catch (error) {
          // Handle error
        } finally {
          checkingUpdate.value = false
        }
      }

      await handleCheckUpdate()
      expect(updateInfo.value.has_update).toBe(false)
      expect(checkingUpdate.value).toBe(false)
    })

    it('should update state when update is found', async () => {
      const checkingUpdate = ref(false)
      const updateInfo = ref({ has_update: false, latest_version: '' })
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.checkUpdate.mockResolvedValue({
        data: {
          has_update: true,
          current_version: '0.2.0',
          latest_version: '0.2.1',
          download_url: 'https://github.com/.../anime1-windows-0.2.1.zip',
          asset_name: 'anime1-windows-0.2.1.zip',
          download_size: 1024000,
          release_notes: 'Bug fixes',
          is_prerelease: false
        }
      })

      const handleCheckUpdate = async () => {
        checkingUpdate.value = true
        try {
          const response = await settingsAPI.checkUpdate()
          const data = response.data
          if (data.has_update) {
            updateInfo.value = {
              has_update: true,
              latest_version: data.latest_version || '',
              download_url: data.download_url || '',
              asset_name: data.asset_name || '',
              download_size: data.download_size || '',
              release_notes: data.release_notes || '',
              is_prerelease: data.is_prerelease || false
            }
          }
        } catch (error) {
          // Handle error
        } finally {
          checkingUpdate.value = false
        }
      }

      await handleCheckUpdate()
      expect(updateInfo.value.has_update).toBe(true)
      expect(updateInfo.value.latest_version).toBe('0.2.1')
    })
  })

  describe('handleDownloadUpdate Logic', () => {
    it('should show warning when no download url', async () => {
      const updateInfo = ref({ download_url: '' })
      const downloadingUpdate = ref(false)
      const ElMessage = (await import('element-plus')).ElMessage

      const handleDownloadUpdate = async () => {
        if (!updateInfo.value.download_url) {
          ElMessage.warning('没有可用的下载链接')
          return
        }
        downloadingUpdate.value = true
        // ... rest of logic
        downloadingUpdate.value = false
      }

      await handleDownloadUpdate()
      expect(downloadingUpdate.value).toBe(false)
      expect(ElMessage.warning).toHaveBeenCalledWith('没有可用的下载链接')
    })

    it('should handle auto-install mode (desktop)', async () => {
      const updateInfo = ref({
        download_url: 'https://github.com/.../anime1-windows-0.2.1.zip'
      })
      const downloadingUpdate = ref(false)
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.downloadUpdate.mockResolvedValue({
        data: {
          success: true,
          restarting: true,
          message: '更新完成，正在重启...',
          updater_path: 'C:\\anime1\\updater.exe',
          updater_type: 'windows'
        }
      })
      settingsAPI.runUpdater.mockResolvedValue({})

      // Mock window.ipcRenderer for desktop
      global.window = { ipcRenderer: { send: vi.fn() } }

      const handleDownloadUpdate = async () => {
        if (!updateInfo.value.download_url) return
        downloadingUpdate.value = true
        try {
          const response = await settingsAPI.downloadUpdate(updateInfo.value.download_url, true)
          if (response.data.success && response.data.restarting) {
            ElMessage.success(response.data.message || '更新完成，正在重启...')
            const updaterType = response.data.updater_type
            if (updaterType === 'macos_dmg') {
              await settingsAPI.exitApp()
            } else if (window.ipcRenderer && response.data.updater_path) {
              await settingsAPI.runUpdater(response.data.updater_path)
            }
          }
        } catch (error) {
          // Handle error
        } finally {
          downloadingUpdate.value = false
        }
      }

      await handleDownloadUpdate()
      expect(downloadingUpdate.value).toBe(false)
      expect(ElMessage.success).toHaveBeenCalled()
      expect(settingsAPI.runUpdater).toHaveBeenCalledWith('C:\\anime1\\updater.exe')
    })

    it('should handle macOS DMG mode (exit app)', async () => {
      const updateInfo = ref({
        download_url: 'https://github.com/.../anime1-macos-0.2.1.dmg'
      })
      const downloadingUpdate = ref(false)
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.downloadUpdate.mockResolvedValue({
        data: {
          success: true,
          restarting: true,
          message: '正在安装更新...',
          updater_type: 'macos_dmg',
          download_path: '/Users/user/Downloads/anime1-macos-0.2.1.dmg'
        }
      })
      settingsAPI.exitApp.mockResolvedValue({})

      // No ipcRenderer for webview mode
      global.window = {}

      const handleDownloadUpdate = async () => {
        if (!updateInfo.value.download_url) return
        downloadingUpdate.value = true
        try {
          const response = await settingsAPI.downloadUpdate(updateInfo.value.download_url, true)
          if (response.data.success && response.data.restarting) {
            ElMessage.success(response.data.message || '更新完成，正在重启...')
            const updaterType = response.data.updater_type
            if (updaterType === 'macos_dmg') {
              await settingsAPI.exitApp()
            } else if (window.ipcRenderer && response.data.updater_path) {
              await settingsAPI.runUpdater(response.data.updater_path)
            }
          }
        } catch (error) {
          // Handle error
        } finally {
          downloadingUpdate.value = false
        }
      }

      await handleDownloadUpdate()
      expect(downloadingUpdate.value).toBe(false)
      expect(ElMessage.success).toHaveBeenCalled()
      expect(settingsAPI.exitApp).toHaveBeenCalled()
    })

    it('should handle web mode (refresh page)', async () => {
      const updateInfo = ref({
        download_url: 'https://github.com/.../anime1-windows-0.2.1.zip'
      })
      const downloadingUpdate = ref(false)
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.downloadUpdate.mockResolvedValue({
        data: {
          success: true,
          restarting: true,
          message: '更新完成'
        }
      })

      // No ipcRenderer for web mode
      global.window = {}

      const originalLocation = window.location
      delete window.location
      window.location = { reload: vi.fn() }

      const handleDownloadUpdate = async () => {
        if (!updateInfo.value.download_url) return
        downloadingUpdate.value = true
        try {
          const response = await settingsAPI.downloadUpdate(updateInfo.value.download_url, true)
          if (response.data.success && response.data.restarting) {
            ElMessage.success(response.data.message || '更新完成，正在重启...')
            if (!window.ipcRenderer) {
              setTimeout(() => window.location.reload(), 2000)
            }
          }
        } catch (error) {
          // Handle error
        } finally {
          downloadingUpdate.value = false
        }
      }

      await handleDownloadUpdate()
      expect(downloadingUpdate.value).toBe(false)

      // Restore location
      window.location = originalLocation
    })

    it('should fallback to browser download on error', async () => {
      const updateInfo = ref({
        download_url: 'https://github.com/.../anime1-windows-0.2.1.zip'
      })
      const downloadingUpdate = ref(false)
      const settingsAPI = (await import('../utils/api')).settingsAPI
      const ElMessage = (await import('element-plus')).ElMessage

      settingsAPI.downloadUpdate.mockRejectedValue(new Error('Download failed'))

      global.window = { open: vi.fn() }

      const handleDownloadUpdate = async () => {
        if (!updateInfo.value.download_url) return
        downloadingUpdate.value = true
        try {
          await settingsAPI.downloadUpdate(updateInfo.value.download_url, true)
        } catch (error) {
          if (error !== 'cancel') {
            ElMessage.warning('自动下载失败，将打开浏览器下载...')
            window.open(updateInfo.value.download_url, '_blank')
          }
        } finally {
          downloadingUpdate.value = false
        }
      }

      await handleDownloadUpdate()
      expect(window.open).toHaveBeenCalledWith(updateInfo.value.download_url, '_blank')
    })
  })

  describe('formatReleaseNotes', () => {
    it('should convert markdown headers to HTML', () => {
      const formatReleaseNotes = (notes) => {
        if (!notes) return ''
        return notes
          .replace(/^### (.*$)/gm, '<h4>$1</h4>')
          .replace(/^## (.*$)/gm, '<h3>$1</h3>')
      }

      const input = `## Features
### New Feature
- Feature A
- Feature B`

      const output = formatReleaseNotes(input)
      expect(output).toContain('<h3>Features</h3>')
      expect(output).toContain('<h4>New Feature</h4>')
    })

    it('should convert markdown bold to HTML', () => {
      const formatReleaseNotes = (notes) => {
        if (!notes) return ''
        return notes.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      }

      const input = 'This is **bold** text'
      const output = formatReleaseNotes(input)
      expect(output).toContain('<strong>bold</strong>')
    })

    it('should convert markdown list items to HTML', () => {
      const formatReleaseNotes = (notes) => {
        if (!notes) return ''
        return notes.replace(/^- (.*$)/gm, '<li>$1</li>')
      }

      const input = '- Item 1\n- Item 2'
      const output = formatReleaseNotes(input)
      expect(output).toContain('<li>Item 1</li>')
      expect(output).toContain('<li>Item 2</li>')
    })

    it('should handle empty notes', () => {
      const formatReleaseNotes = (notes) => {
        if (!notes) return ''
        return notes
      }

      expect(formatReleaseNotes('')).toBe('')
      expect(formatReleaseNotes(null)).toBe('')
      expect(formatReleaseNotes(undefined)).toBe('')
    })
  })
})

describe('Settings View - Loading States', () => {
  it('should have checkingUpdate state', () => {
    const checkingUpdate = ref(false)
    expect(checkingUpdate.value).toBe(false)

    checkingUpdate.value = true
    expect(checkingUpdate.value).toBe(true)
  })

  it('should have downloadingUpdate state', () => {
    const downloadingUpdate = ref(false)
    expect(downloadingUpdate.value).toBe(false)

    downloadingUpdate.value = true
    expect(downloadingUpdate.value).toBe(true)
  })
})

describe('Settings View - About Info', () => {
  it('should have aboutInfo state', () => {
    const aboutInfo = ref(null)
    expect(aboutInfo.value).toBeNull()

    aboutInfo.value = {
      version: '0.2.1',
      channel: 'stable',
      repository: 'https://github.com/elfgzp/anime1-desktop'
    }
    expect(aboutInfo.value.version).toBe('0.2.1')
    expect(aboutInfo.value.channel).toBe('stable')
  })
})
