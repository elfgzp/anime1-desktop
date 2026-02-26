const { test, expect } = require('@playwright/test');
const { resolve } = require('path');

/**
 * IPC 功能验证测试 - CommonJS 版本
 */
test.describe('IPC 功能验证', () => {
  test('验证 IPC API 可用性', async () => {
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

    // 等待窗口创建
    const window = await electronApp.firstWindow();
    
    // 等待页面加载
    await window.waitForLoadState('domcontentloaded');
    
    // 验证 IPC API 可用
    const hasApi = await window.evaluate(() => {
      return typeof window.api !== 'undefined';
    });
    
    expect(hasApi).toBe(true);
    
    if (hasApi) {
      // 获取可用 API 列表
      const apiKeys = await window.evaluate(() => {
        return Object.keys(window.api || {});
      });
      
      console.log('✅ 可用 API:', apiKeys);
      
      // 验证核心 API 存在
      expect(apiKeys).toContain('anime');
      expect(apiKeys).toContain('favorite');
      expect(apiKeys).toContain('history');
      expect(apiKeys).toContain('settings');
      expect(apiKeys).toContain('download');
      
      // 验证 anime API 方法
      const animeApiMethods = await window.evaluate(() => {
        return Object.keys(window.api.anime || {});
      });
      
      console.log('✅ Anime API 方法:', animeApiMethods);
      
      expect(animeApiMethods).toContain('getList');
      expect(animeApiMethods).toContain('getDetail');
      expect(animeApiMethods).toContain('search');
      expect(animeApiMethods).toContain('parsePwEpisodes'); // 新添加的
    }
    
    // 关闭应用
    await electronApp.close();
  });

  test('验证番剧列表获取', async () => {
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
    
    // 等待 IPC 初始化
    await window.waitForTimeout(2000);
    
    // 调用 anime:list API
    const result = await window.evaluate(async () => {
      try {
        return await window.api.anime.getList({ page: 1, pageSize: 10 });
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 番剧列表结果:', JSON.stringify(result, null, 2).substring(0, 500));
    
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.data.animeList).toBeDefined();
    expect(result.data.animeList.length).toBeGreaterThan(0);
    
    await electronApp.close();
  });

  test('验证收藏功能', async () => {
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
    
    // 测试获取收藏列表
    const result = await window.evaluate(async () => {
      try {
        return await window.api.favorite.getList();
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 收藏列表结果:', JSON.stringify(result, null, 2).substring(0, 300));
    
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data)).toBe(true);
    
    await electronApp.close();
  });

  test('验证播放历史功能', async () => {
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
    
    // 测试获取播放历史
    const result = await window.evaluate(async () => {
      try {
        return await window.api.history.getList({ limit: 10 });
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 播放历史结果:', JSON.stringify(result, null, 2).substring(0, 300));
    
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(Array.isArray(result.data)).toBe(true);
    
    // 测试新增的历史功能
    const hasDeleteMethod = await window.evaluate(() => {
      return typeof window.api.history.delete === 'function';
    });
    
    expect(hasDeleteMethod).toBe(true);
    console.log('✅ history:delete 方法存在');
    
    await electronApp.close();
  });
});
