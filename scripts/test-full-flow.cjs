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
    await window.waitForTimeout(8000);
    
    // 在主进程中执行代码检查 animeCache
    const mainProcessData = await electronApp.evaluate(async () => {
      // 这里无法直接访问主进程数据，需要通过 IPC
      return { message: 'Need to check main process logs' };
    });
    
    // 检查 API 返回的数据
    const apiData = await window.evaluate(async () => {
      const response = await window.api.anime.getList({ page: 1 });
      const anime = response.data?.animeList?.find(a => a.id === '1782');
      return {
        id: anime?.id,
        title: anime?.title,
        coverUrl: anime?.coverUrl
      };
    });
    
    console.log('API 返回的数据:', apiData);
    
    // 等待几秒再检查
    await window.waitForTimeout(5000);
    
    const apiData2 = await window.evaluate(async () => {
      const response = await window.api.anime.getList({ page: 1 });
      const anime = response.data?.animeList?.find(a => a.id === '1782');
      return {
        id: anime?.id,
        title: anime?.title,
        coverUrl: anime?.coverUrl
      };
    });
    
    console.log('5秒后 API 返回的数据:', apiData2);
    
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
