const { _electron } = require('playwright-core');
const path = require('path');

async function test() {
  const electronApp = await _electron.launch({
    args: [
      path.join(__dirname, '../dist-electron/main/index.js'),
      '--no-sandbox'
    ],
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(3000);
    
    console.log('[Test] 等待首页加载...');
    
    // 点击第一个番剧卡片进入详情页
    const firstCard = await window.locator('.anime-card').first();
    await firstCard.click();
    
    console.log('[Test] 已进入详情页');
    await window.waitForTimeout(2000);
    
    // 检查是否有剧集列表
    const episodeList = await window.locator('.episode-list').count();
    console.log(`[Test] 剧集列表存在: ${episodeList > 0}`);
    
    if (episodeList > 0) {
      // 点击第一集
      const firstEpisode = await window.locator('.episode-item').first();
      await firstEpisode.click();
      console.log('[Test] 已点击第一集');
      
      await window.waitForTimeout(3000);
      
      // 检查视频播放器状态
      const videoPlayer = await window.locator('video').count();
      console.log(`[Test] 视频播放器存在: ${videoPlayer > 0}`);
      
      if (videoPlayer > 0) {
        const videoSrc = await window.locator('video').evaluate(el => el.src);
        console.log(`[Test] 视频 URL: ${videoSrc ? videoSrc.substring(0, 50) + '...' : 'empty'}`);
        
        // 等待视频加载
        await window.waitForTimeout(3000);
        
        // 检查视频是否可播放
        const videoReady = await window.locator('video').evaluate(el => el.readyState);
        console.log(`[Test] 视频 readyState: ${videoReady}`);
      }
    }
    
    // 截图
    await window.screenshot({ path: 'screenshots/detail-test.png' });
    console.log('[Test] 截图已保存');
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
