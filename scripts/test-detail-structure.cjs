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
    await window.locator('.anime-card').first().click();
    await window.waitForTimeout(3000);
    
    // 检查页面结构
    const structure = await window.evaluate(() => {
      return {
        html: document.body.innerHTML.substring(0, 2000),
        episodeSection: document.querySelector('.episode-section')?.outerHTML?.substring(0, 500) || 'not found',
        episodeList: document.querySelector('.episode-list')?.outerHTML?.substring(0, 500) || 'not found',
        episodes: Array.from(document.querySelectorAll('.episode-item')).map(el => el.textContent)
      };
    });
    
    console.log('[Test] Episode section:', structure.episodeSection);
    console.log('[Test] Episode list:', structure.episodeList);
    console.log('[Test] Episodes:', structure.episodes);
    
  } catch (e) {
    console.error('[Test] Error:', e.message);
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
