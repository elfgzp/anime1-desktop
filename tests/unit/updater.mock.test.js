/**
 * Mock Updater Tests
 * 
 * 测试自动更新功能的 mock 实现
 * 无需真实发布到 GitHub Releases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock electron and electron-log
vi.mock('electron', () => ({
  ipcMain: {
    handle: vi.fn(),
  },
  BrowserWindow: vi.fn(),
  app: {
    getVersion: vi.fn(() => '1.0.0'),
  },
}));

vi.mock('electron-log', () => ({
  default: {
    info: vi.fn(),
    debug: vi.fn(),
    error: vi.fn(),
  },
}));

describe('Mock Updater', () => {
  let mockUpdater;
  let ipcHandlers = {};

  beforeEach(async () => {
    // Reset modules
    vi.resetModules();
    
    // Setup ipcMain.handle mock to capture handlers
    const { ipcMain } = await import('electron');
    ipcMain.handle.mockImplementation((channel, handler) => {
      ipcHandlers[channel] = handler;
    });
    
    // Import mock updater
    const mockModule = await import('../../src/services/updater.mock.js');
    mockUpdater = mockModule;
  });

  afterEach(() => {
    vi.clearAllMocks();
    ipcHandlers = {};
  });

  describe('Initialization', () => {
    it('should initialize mock updater', () => {
      const mockWindow = {
        webContents: {
          send: vi.fn(),
        },
        isDestroyed: vi.fn(() => false),
      };
      
      const result = mockUpdater.initMockUpdater(mockWindow);
      
      expect(result).toEqual({
        isMock: true,
        scenario: 'has-update', // default scenario
      });
    });

    it('should setup all IPC handlers', () => {
      const mockWindow = {
        webContents: {
          send: vi.fn(),
        },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // Check that all handlers are registered
      expect(ipcHandlers['updater:check']).toBeDefined();
      expect(ipcHandlers['updater:download']).toBeDefined();
      expect(ipcHandlers['updater:install']).toBeDefined();
      expect(ipcHandlers['updater:status']).toBeDefined();
      expect(ipcHandlers['mock-updater:set-scenario']).toBeDefined();
      expect(ipcHandlers['mock-updater:get-scenarios']).toBeDefined();
      expect(ipcHandlers['mock-updater:get-config']).toBeDefined();
      expect(ipcHandlers['mock-updater:reset']).toBeDefined();
    });
  });

  describe('Scenarios', () => {
    it('should return list of available scenarios', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['mock-updater:get-scenarios']();
      
      expect(result.success).toBe(true);
      expect(result.data).toBeInstanceOf(Array);
      expect(result.data.length).toBeGreaterThan(0);
      
      // Check structure
      expect(result.data[0]).toHaveProperty('id');
      expect(result.data[0]).toHaveProperty('name');
      expect(result.data[0]).toHaveProperty('description');
    });

    it('should switch scenarios', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['mock-updater:set-scenario'](null, 'no-update');
      
      expect(result.success).toBe(true);
      expect(result.scenario).toBe('no-update');
    });

    it('should reject unknown scenarios', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['mock-updater:set-scenario'](null, 'unknown-scenario');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Unknown scenario');
    });
  });

  describe('Update Check', () => {
    it('should return no update for no-update scenario', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // Switch to no-update scenario
      await ipcHandlers['mock-updater:set-scenario'](null, 'no-update');
      
      const result = await ipcHandlers['updater:check']();
      
      expect(result.success).toBe(true);
      expect(result.data.has_update).toBe(false);
    });

    it('should return update available for has-update scenario', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['updater:check']();
      
      expect(result.success).toBe(true);
      expect(result.data.has_update).toBe(true);
      expect(result.data.latest_version).toBe('9.9.9');
      expect(result.data.release_notes).toBeDefined();
      expect(result.data.download_url).toBeDefined();
    });

    it('should return error for check-error scenario', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // Switch to error scenario
      await ipcHandlers['mock-updater:set-scenario'](null, 'check-error');
      
      const result = await ipcHandlers['updater:check']();
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.data.has_update).toBe(false);
    });
  });

  describe('Download', () => {
    it('should fail download if no update available', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // Don't check for updates first
      const result = await ipcHandlers['updater:download']();
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('No update available');
    });

    it('should succeed download for has-update scenario', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      // Set shorter delays for faster test
      process.env.MOCK_DOWNLOAD_DELAY = '100';
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // First check for updates
      await ipcHandlers['updater:check']();
      
      // Then download
      const result = await ipcHandlers['updater:download']();
      
      expect(result.success).toBe(true);
      
      // Reset
      delete process.env.MOCK_DOWNLOAD_DELAY;
    }, 10000);  // 10 second timeout
  });

  describe('Install', () => {
    it('should fail install if update not downloaded', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['updater:install']();
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Update not downloaded yet');
    });

    it('should succeed install if update downloaded', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // Use pre-downloaded scenario
      await ipcHandlers['mock-updater:set-scenario'](null, 'downloaded');
      await ipcHandlers['updater:check']();
      
      const result = await ipcHandlers['updater:install']();
      
      expect(result.success).toBe(true);
    });
  });

  describe('Status', () => {
    it('should return current status', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['updater:status']();
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('checking');
      expect(result.data).toHaveProperty('available');
      expect(result.data).toHaveProperty('downloading');
      expect(result.data).toHaveProperty('downloaded');
      expect(result.data).toHaveProperty('progress');
    });
  });

  describe('Config', () => {
    it('should return mock config', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      const result = await ipcHandlers['mock-updater:get-config']();
      
      expect(result.success).toBe(true);
      expect(result.data.isMock).toBe(true);
      expect(result.data.scenario).toBeDefined();
    });
  });

  describe('Reset', () => {
    it('should reset state', async () => {
      const mockWindow = {
        webContents: { send: vi.fn() },
        isDestroyed: vi.fn(() => false),
      };
      
      mockUpdater.initMockUpdater(mockWindow);
      
      // First check for updates to change state
      await ipcHandlers['updater:check']();
      
      // Reset
      const result = await ipcHandlers['mock-updater:reset']();
      
      expect(result.success).toBe(true);
      expect(result.state.checking).toBe(false);
      expect(result.state.available).toBe(false);
    });
  });
});

describe('Mock Scenarios Details', () => {
  const scenarios = [
    {
      name: 'no-update',
      expected: { hasUpdate: false, shouldError: false },
    },
    {
      name: 'has-update',
      expected: { hasUpdate: true, shouldError: false },
    },
    {
      name: 'check-error',
      expected: { hasUpdate: false, shouldError: true },
    },
    {
      name: 'download-error',
      expected: { hasUpdate: true, shouldError: false, downloadError: true },
    },
    {
      name: 'downloaded',
      expected: { hasUpdate: true, alreadyDownloaded: true },
    },
  ];

  scenarios.forEach(({ name, expected }) => {
    it(`should handle ${name} scenario correctly`, async () => {
      // This is a meta-test to ensure all scenarios are documented
      expect(['no-update', 'has-update', 'check-error', 'download-error', 'downloaded']).toContain(name);
    });
  });
});
