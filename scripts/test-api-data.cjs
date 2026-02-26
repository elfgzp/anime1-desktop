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
    
    // 直接调用 API
    const apiResult = await window.evaluate(async () => {
      const response = await window.api.anime.getList({ page: 1 });
      const animeList = response.data?.animeList || [];
      return animeList.slice(0, 3).map(a => ({
        title: a.title?.substring(0, 20),
        coverUrl: a.coverUrl,
        id: a.id
      }));
    });
    
    console.log('[Test] API返回的数据:');
    for (const item of apiResult) {
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
