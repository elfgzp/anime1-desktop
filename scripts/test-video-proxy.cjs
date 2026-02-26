const { _electron } = require('playwright-core');
const path = require('path');

async function test() {
  const electronApp = await _electron.launch({
    args: [
      path.join(__dirname, '../dist-electron/main/index.js'),
      '--no-sandbox'
    ],
  });

  // 捕获主进程日志
  electronApp.on('console', msg => {
    console.log('[Main]', msg.text());
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(3000);
    
    // 点击第一个番剧卡片
    await window.locator('.anime-card').first().click();
    await window.waitForTimeout(3000);
    
    // 点击第一集
    await window.locator('.episode-card').first().click();
    await window.waitForTimeout(3000);
    
    // 检查 videoUrl
    const videoUrl = await window.evaluate(() => {
      // 从 Vue 组件获取 videoUrl
      const videoEl = document.querySelector('video');
      return {
        videoSrc: videoEl?.src || 'no video src',
        videoError: document.querySelector('.video-error')?.textContent || 'no error',
        videoLoading: document.querySelector('.video-loading')?.textContent || 'not loading'
      };
    });
    
    console.log('[Test] Video info:', videoUrl);
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
