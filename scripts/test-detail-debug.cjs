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
    
    // 点击第一个番剧卡片
    const firstCard = await window.locator('.anime-card').first();
    await firstCard.click();
    
    console.log('[Test] 已进入详情页');
    await window.waitForTimeout(2000);
    
    // 获取页面 HTML 结构
    const html = await window.evaluate(() => {
      const episodeSection = document.querySelector('.episode-section');
      const videoPlayer = document.querySelector('video');
      return {
        episodeSectionHTML: episodeSection ? episodeSection.outerHTML.substring(0, 500) : 'not found',
        videoPlayerHTML: videoPlayer ? videoPlayer.outerHTML : 'not found',
        errorMessage: document.querySelector('.video-error')?.textContent || 'no error'
      };
    });
    
    console.log('[Test] 剧集区域:', html.episodeSectionHTML);
    console.log('[Test] 视频播放器:', html.videoPlayerHTML);
    console.log('[Test] 错误信息:', html.errorMessage);
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
