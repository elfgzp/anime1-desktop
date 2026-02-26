const { test, expect } = require('@playwright/test');
const { resolve } = require('path');

/**
 * 自动下载功能验证测试
 */
test.describe('自动下载功能验证', () => {
  test('验证自动下载配置 API', async () => {
    const { _electron: electron } = require('@playwright/test');
    
    const mainPath = resolve(__dirname, '../../dist-electron/main/index.js');
    
    const electronApp = await electron.launch({
      args: [mainPath, '--no-sandbox'],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
      },
    });

    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(2000);

    // 测试获取配置
    const configResult = await window.evaluate(async () => {
      try {
        return await window.api.autoDownload.getConfig();
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 自动下载配置:', JSON.stringify(configResult, null, 2).substring(0, 300));
    
    expect(configResult).toBeDefined();
    expect(configResult.success).toBe(true);
    expect(configResult.data).toBeDefined();
    expect(typeof configResult.data.enabled).toBe('boolean');
    expect(typeof configResult.data.autoDownloadNew).toBe('boolean');
    expect(typeof configResult.data.autoDownloadFavorites).toBe('boolean');
    expect(configResult.data.filters).toBeDefined();
    
    await electronApp.close();
  });

  test('验证自动下载状态 API', async () => {
    const { _electron: electron } = require('@playwright/test');
    
    const mainPath = resolve(__dirname, '../../dist-electron/main/index.js');
    
    const electronApp = await electron.launch({
      args: [mainPath, '--no-sandbox'],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
      },
    });

    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(2000);

    // 测试获取状态
    const statusResult = await window.evaluate(async () => {
      try {
        return await window.api.autoDownload.getStatus();
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 自动下载状态:', JSON.stringify(statusResult, null, 2).substring(0, 400));
    
    expect(statusResult).toBeDefined();
    expect(statusResult.success).toBe(true);
    expect(statusResult.data).toBeDefined();
    expect(typeof statusResult.data.enabled).toBe('boolean');
    expect(typeof statusResult.data.running).toBe('boolean');
    expect(statusResult.data.statusCounts).toBeDefined();
    expect(Array.isArray(statusResult.data.recentDownloads)).toBe(true);
    
    await electronApp.close();
  });

  test('验证筛选预览 API', async () => {
    const { _electron: electron } = require('@playwright/test');
    
    const mainPath = resolve(__dirname, '../../dist-electron/main/index.js');
    
    const electronApp = await electron.launch({
      args: [mainPath, '--no-sandbox'],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
      },
    });

    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(2000);

    // 测试筛选预览
    const previewResult = await window.evaluate(async () => {
      try {
        return await window.api.autoDownload.previewFilter({
          filters: {
            minYear: 2024,
            specificYears: [],
            seasons: ['冬季'],
            includePatterns: [],
            excludePatterns: []
          }
        });
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 筛选预览:', JSON.stringify(previewResult, null, 2).substring(0, 300));
    
    expect(previewResult).toBeDefined();
    expect(previewResult.success).toBe(true);
    expect(previewResult.data).toBeDefined();
    expect(typeof previewResult.data.totalAnime).toBe('number');
    expect(typeof previewResult.data.matchedCount).toBe('number');
    expect(Array.isArray(previewResult.data.matchedAnime)).toBe(true);
    
    await electronApp.close();
  });
});
