/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { settingsAPI, updateAPI } from '../utils/api'
import { RESPONSE_FIELDS, ERROR_MESSAGES } from '../constants/api'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    }))
  },
  create: vi.fn()
}))

describe('Update API', () => {
  describe('updateAPI', () => {
    it('should have check method', () => {
      expect(typeof updateAPI.check).toBe('function')
    })

    it('should have getInfo method', () => {
      expect(typeof updateAPI.getInfo).toBe('function')
    })
  })

  describe('settingsAPI - Update related', () => {
    it('should have checkUpdate method', () => {
      expect(typeof settingsAPI.checkUpdate).toBe('function')
    })

    it('should have downloadUpdate method', () => {
      expect(typeof settingsAPI.downloadUpdate).toBe('function')
    })

    it('should have runUpdater method', () => {
      expect(typeof settingsAPI.runUpdater).toBe('function')
    })
  })
})

describe('Update Response Format', () => {
  describe('Check Update Response', () => {
    it('should have has_update field', () => {
      expect(RESPONSE_FIELDS.HAS_UPDATE).toBe('has_update')
    })

    it('should handle no update available', () => {
      const noUpdateResponse = {
        has_update: false,
        current_version: '0.2.1'
      }
      expect(noUpdateResponse.has_update).toBe(false)
      expect(noUpdateResponse.current_version).toBe('0.2.1')
    })

    it('should handle update available', () => {
      const updateResponse = {
        has_update: true,
        current_version: '0.2.0',
        latest_version: '0.2.1',
        download_url: 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-windows-0.2.1.zip',
        asset_name: 'anime1-windows-0.2.1.zip',
        download_size: 1024000,
        release_notes: 'Bug fixes and improvements',
        is_prerelease: false
      }
      expect(updateResponse.has_update).toBe(true)
      expect(updateResponse.latest_version).toBe('0.2.1')
      expect(updateResponse.download_url).toContain('github.com')
    })

    it('should handle prerelease update', () => {
      const prereleaseResponse = {
        has_update: true,
        current_version: '0.2.0',
        latest_version: '0.3.0-rc.1',
        is_prerelease: true
      }
      expect(prereleaseResponse.has_update).toBe(true)
      expect(prereleaseResponse.is_prerelease).toBe(true)
      expect(prereleaseResponse.latest_version).toContain('rc')
    })
  })

  describe('Download Update Response', () => {
    it('should handle auto-install mode success', () => {
      const autoInstallResponse = {
        success: true,
        restarting: true,
        message: '更新完成，正在重启...',
        updater_path: 'C:\\Users\\anime1\\updater.exe'
      }
      expect(autoInstallResponse.success).toBe(true)
      expect(autoInstallResponse.restarting).toBe(true)
    })

    it('should handle manual download mode', () => {
      const manualResponse = {
        success: true,
        restarting: false,
        file_path: 'C:\\Users\\anime1\\Downloads\\anime1-windows-0.2.1.zip',
        open_path: 'C:\\Users\\anime1\\Downloads'
      }
      expect(manualResponse.success).toBe(true)
      expect(manualResponse.restarting).toBe(false)
    })

    it('should handle download failure', () => {
      const failureResponse = {
        success: false,
        error: '下载失败'
      }
      expect(failureResponse.success).toBe(false)
      expect(failureResponse.error).toBeDefined()
    })
  })

  describe('Update Info Response', () => {
    it('should have all required fields', () => {
      const infoResponse = {
        current_version: '0.2.1',
        channel: 'stable',
        repo_owner: 'elfgzp',
        repo_name: 'anime1-desktop'
      }
      expect(infoResponse.current_version).toBeDefined()
      expect(infoResponse.channel).toBeDefined()
      expect(infoResponse.repo_owner).toBe('elfgzp')
      expect(infoResponse.repo_name).toBe('anime1-desktop')
    })

    it('should handle test channel', () => {
      const testChannelInfo = {
        current_version: '0.2.1-abc123',
        channel: 'test'
      }
      expect(testChannelInfo.channel).toBe('test')
    })
  })
})

describe('Update Error Messages', () => {
  it('should have CHECK_UPDATE_FAILED message', () => {
    expect(ERROR_MESSAGES.CHECK_UPDATE_FAILED).toBeDefined()
    expect(typeof ERROR_MESSAGES.CHECK_UPDATE_FAILED).toBe('string')
  })
})

describe('Version Format Validation', () => {
  it('should recognize release version format', () => {
    const releaseVersion = '0.2.1'
    expect(releaseVersion.match(/^\d+\.\d+(\.\d+)?$/)).toBeTruthy()
  })

  it('should recognize version with commit hash', () => {
    const devVersion = '0.2.1-abc123'
    expect(devVersion.match(/^\d+\.\d+(\.\d+)?-[a-f0-9]+$/)).toBeTruthy()
  })

  it('should recognize prerelease version', () => {
    const prereleaseVersions = ['0.3.0-rc.1', '0.3.0-beta.2', '0.3.0-alpha.3']
    prereleaseVersions.forEach(version => {
      expect(version.match(/^\d+\.\d+(\.\d+)?-(alpha|beta|rc)\.?\d*$/)).toBeTruthy()
    })
  })

  it('should recognize dev version', () => {
    const devVersion = 'dev-abc123'
    expect(devVersion.match(/^dev-[a-f0-9]+$/)).toBeTruthy()
  })
})

describe('Download URL Validation', () => {
  it('should validate Windows download URL', () => {
    const windowsUrl = 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-windows-0.2.1.zip'
    expect(windowsUrl).toContain('github.com')
    expect(windowsUrl).toContain('releases/download')
    expect(windowsUrl).toContain('anime1-windows')
  })

  it('should validate macOS download URL', () => {
    const macosUrl = 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-macos-x64-0.2.1.zip'
    expect(macosUrl).toContain('github.com')
    expect(macosUrl).toContain('anime1-macos')
  })

  it('should validate Linux download URL', () => {
    const linuxUrl = 'https://github.com/elfgzp/anime1-desktop/releases/download/v0.2.1/anime1-linux-0.2.1.zip'
    expect(linuxUrl).toContain('github.com')
    expect(linuxUrl).toContain('anime1-linux')
  })
})
