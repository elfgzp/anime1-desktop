const { _electron } = require('playwright-core');
const path = require('path');

async function test() {
  const electronApp = await _electron.launch({
    args: [
      path.join(__dirname, '../dist-electron/main/index.js'),
      '--no-sandbox'
    ],
  });

  // 捕获主进程控制台输出
  electronApp.on('console', msg => {
    console.log('[Main]', msg.text());
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    await window.waitForTimeout(5000);
    
    // 调用 API
    const apiData = await window.evaluate(async () => {
      const response = await window.api.anime.getList({ page: 1 });
      const anime = response.data?.animeList?.[0];
      return {
        id: anime?.id,
        title: anime?.title,
        coverUrl: anime?.coverUrl
      };
    });
    
    console.log('API 返回:', apiData);
    
    await window.waitForTimeout(3000);
    
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
