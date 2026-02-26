#!/usr/bin/env node
/**
 * 简单直接的 Electron 测试脚本
 * 用于验证 window.api 是否正常工作
 */

const { _electron: electron } = require('playwright-core');
const path = require('path');

async function testElectron() {
  console.log('[Test] Starting Electron app...');
  
  const mainPath = path.resolve(__dirname, '../dist-electron/main/index.js');
  console.log('[Test] Main path:', mainPath);
  
  let electronApp = null;
  
  try {
    // 启动 Electron
    electronApp = await electron.launch({
      args: [mainPath, '--no-sandbox'],
      env: {
        ...process.env,
        NODE_ENV: 'test',
        E2E_TEST: 'true',
        DISABLE_UPDATE_CHECK: 'true',
      },
      timeout: 60000,
    });

    console.log('[Test] Electron launched, waiting for window...');
    
    // 等待第一个窗口
    const window = await electronApp.firstWindow();
    console.log('[Test] Window created, URL:', await window.url());
    
    // 等待页面加载
    await window.waitForLoadState('domcontentloaded', { timeout: 15000 });
    console.log('[Test] DOM content loaded');
    
    // 等待 preload 执行
    await new Promise(r => setTimeout(r, 3000));
    
    // 检查 window.api
    console.log('[Test] Checking window.api...');
    const hasApi = await window.evaluate(() => {
      return typeof window.api !== 'undefined';
    });
    
    console.log('[Test] window.api exists:', hasApi);
    
    if (hasApi) {
      // 检查 API 方法
      const apiMethods = await window.evaluate(() => {
        const api = window.api;
        return {
          hasWindow: typeof api?.window !== 'undefined',
          hasAnime: typeof api?.anime !== 'undefined',
          hasFavorite: typeof api?.favorite !== 'undefined',
          hasHistory: typeof api?.history !== 'undefined',
          hasSettings: typeof api?.settings !== 'undefined',
          hasDownload: typeof api?.download !== 'undefined',
          hasSystem: typeof api?.system !== 'undefined',
          hasUpdate: typeof api?.update !== 'undefined',
          windowMethods: Object.keys(api?.window || {}),
          animeMethods: Object.keys(api?.anime || {}),
        };
      });
      
      console.log('[Test] API structure:', JSON.stringify(apiMethods, null, 2));
      
      // 测试具体 API
      console.log('[Test] Testing window.api.anime.getList...');
      const listResult = await window.evaluate(async () => {
        try {
          const response = await window.api.anime.getList({ page: 1 });
          const animeList = response.data?.animeList || [];
          // 获取前 3 个番剧的封面 URL
          const coverUrls = animeList.slice(0, 3).map(a => ({ 
            title: a.title?.substring(0, 20), 
            coverUrl: a.coverUrl 
          }));
          return { 
            success: response.success, 
            hasData: !!response.data,
            animeCount: animeList.length,
            coverUrls
          };
        } catch (e) {
          return { success: false, error: e.message };
        }
      });
      
      console.log('[Test] getList result:', listResult);
      
      // 验证封面 URL 格式
      if (listResult.coverUrls) {
        console.log('[Test] Checking cover URLs:');
        for (const item of listResult.coverUrls) {
          const isLarge = item.coverUrl?.includes('/l/');
          const isCommon = item.coverUrl?.includes('/c/');
          console.log(`  - ${item.title}: ${isLarge ? '✅ /l/' : isCommon ? '⚠️ /c/' : '❓ other'} - ${item.coverUrl?.substring(0, 60)}...`);
        }
      }
      
      // 测试收藏 API
      console.log('[Test] Testing window.api.favorite.getList...');
      const favResult = await window.evaluate(async () => {
        try {
          const response = await window.api.favorite.getList();
          return { success: response.success, count: response.data?.length || 0 };
        } catch (e) {
          return { success: false, error: e.message };
        }
      });
      
      console.log('[Test] favorite.getList result:', favResult);
      
      // 截图
      const screenshotPath = path.resolve(__dirname, '../screenshots/electron-test.png');
      await window.screenshot({ path: screenshotPath });
      console.log('[Test] Screenshot saved to:', screenshotPath);
      
      // 最终判断
      if (hasApi && listResult.success && favResult.success) {
        console.log('\n✅ ALL TESTS PASSED!');
        console.log('- window.api is defined');
        console.log('- anime.getList works');
        console.log('- favorite.getList works');
      } else {
        console.log('\n❌ SOME TESTS FAILED!');
        if (!hasApi) console.log('  - window.api is undefined');
        if (!listResult.success) console.log('  - anime.getList failed:', listResult.error);
        if (!favResult.success) console.log('  - favorite.getList failed:', favResult.error);
      }
    } else {
      console.log('\n❌ FAILED: window.api is undefined!');
      console.log('This means the preload script is not working correctly.');
    }

  } catch (error) {
    console.error('[Test] Error:', error.message);
    console.error(error.stack);
  } finally {
    if (electronApp) {
      console.log('[Test] Closing Electron app...');
      await electronApp.close();
    }
  }
}

testElectron().catch(console.error);
