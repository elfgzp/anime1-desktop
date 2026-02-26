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
    await window.waitForTimeout(5000);
    
    // 检查 store 中的数据
    const storeData = await window.evaluate(async () => {
      // 等待 store 加载
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 获取 animeList
      const animeList = window.useAnimeStore?.().animeList || [];
      return animeList.slice(0, 3).map(a => ({
        title: a.title?.substring(0, 20),
        coverUrl: a.coverUrl,
        id: a.id
      }));
    });
    
    console.log('[Test] Store data:');
    for (const item of storeData) {
      const isLarge = item.coverUrl?.includes('/l/');
      const isCommon = item.coverUrl?.includes('/c/');
      console.log(`  - ${item.title}: ${isLarge ? '✅ /l/' : isCommon ? '⚠️ /c/' : '❓ other'}`);
      console.log(`    URL: ${item.coverUrl}`);
    }
    
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
