const { test, expect } = require('@playwright/test');
const { resolve } = require('path');

/**
 * 更新功能验证测试
 */
test.describe('更新功能验证', () => {
  test('验证更新检查 API', async () => {
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

    // 测试检查更新
    const result = await window.evaluate(async () => {
      try {
        return await window.api.update.check();
      } catch (e) {
        return { error: e.message };
      }
    });
    
    console.log('✅ 更新检查结果:', JSON.stringify(result, null, 2));
    
    expect(result).toBeDefined();
    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(typeof result.data.hasUpdate).toBe('boolean');
    expect(typeof result.data.currentVersion).toBe('string');
    
    await electronApp.close();
  });

  test('验证 update API 存在', async () => {
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

    // 验证 update API 存在
    const hasUpdateApi = await window.evaluate(() => {
      return typeof window.api.update !== 'undefined';
    });
    
    expect(hasUpdateApi).toBe(true);
    
    // 验证各个方法存在
    const methods = await window.evaluate(() => {
      return {
        check: typeof window.api.update.check,
        download: typeof window.api.update.download,
        install: typeof window.api.update.install
      };
    });
    
    console.log('✅ Update API 方法:', methods);
    expect(methods.check).toBe('function');
    expect(methods.download).toBe('function');
    expect(methods.install).toBe('function');
    
    await electronApp.close();
  });
});
