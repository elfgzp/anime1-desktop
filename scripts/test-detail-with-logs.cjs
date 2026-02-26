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
    const text = msg.text();
    if (text.includes('[Anime1]') || text.includes('[HTTP]') || text.includes('extractVideo') || text.includes('403')) {
      console.log('[Main]', text);
    }
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(3000);
    
    // 点击第一个番剧卡片
    const firstCard = await window.locator('.anime-card').first();
    await firstCard.click();
    
    console.log('[Test] 已进入详情页，等待剧集加载...');
    await window.waitForTimeout(3000);
    
    // 等待视频错误出现
    await window.waitForTimeout(2000);
    
    // 获取页面上的错误信息
    const errorText = await window.evaluate(() => {
      const errorEl = document.querySelector('.video-error');
      return errorEl ? errorEl.textContent : 'no error element';
    });
    
    console.log('[Test] 视频错误:', errorText);
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
