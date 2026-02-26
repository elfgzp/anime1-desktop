const { _electron } = require('playwright-core');
const path = require('path');

async function testCoverUrl() {
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
    
    // 获取页面上实际显示的图片 URL
    const imgSrcs = await window.evaluate(() => {
      const imgs = document.querySelectorAll('.anime-card .cover-image');
      return Array.from(imgs).slice(0, 3).map(img => ({
        src: img.src,
        isLoaded: img.complete,
        naturalWidth: img.naturalWidth
      }));
    });
    
    console.log('[Test] Actual image elements on page:');
    for (const img of imgSrcs) {
      const isLarge = img.src?.includes('/l/');
      const isCommon = img.src?.includes('/c/');
      console.log(`  - ${isLarge ? '✅ /l/' : isCommon ? '⚠️ /c/' : '❓ other'} width=${img.naturalWidth}px`);
      console.log(`    src: ${img.src?.substring(0, 80)}...`);
    }
    
  } finally {
    await electronApp.close();
  }
}

testCoverUrl().catch(console.error);
