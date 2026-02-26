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
    if (text.includes('[Anime1]') || text.includes('video') || text.includes('proxy')) {
      console.log('[Main]', text);
    }
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(3000);
    
    console.log('[Test] 点击第一个番剧卡片...');
    const firstCard = await window.locator('.anime-card').first();
    await firstCard.click();
    
    console.log('[Test] 等待详情页加载...');
    await window.waitForTimeout(3000);
    
    // 查找并点击剧集
    console.log('[Test] 查找剧集...');
    const episodeCards = await window.locator('.episode-card').count();
    console.log(`[Test] 找到 ${episodeCards} 个剧集`);
    
    if (episodeCards > 0) {
      console.log('[Test] 点击第一集...');
      await window.locator('.episode-card').first().click();
      
      console.log('[Test] 等待视频加载...');
      await window.waitForTimeout(5000);
      
      // 检查视频状态
      const videoInfo = await window.evaluate(() => {
        const video = document.querySelector('video');
        return {
          hasVideo: !!video,
          src: video?.src?.substring(0, 100) || 'no src',
          readyState: video?.readyState || 0,
          error: video?.error?.message || 'no error'
        };
      });
      
      console.log('[Test] 视频状态:', videoInfo);
      
      // 截图
      await window.screenshot({ path: 'screenshots/video-playback-test.png' });
      console.log('[Test] 截图已保存');
    } else {
      console.log('[Test] 没有找到剧集，截图查看...');
      await window.screenshot({ path: 'screenshots/no-episodes.png' });
    }
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
