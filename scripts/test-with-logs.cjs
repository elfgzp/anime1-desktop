const { _electron } = require('playwright-core');
const path = require('path');

async function test() {
  const electronApp = await _electron.launch({
    args: [
      path.join(__dirname, '../dist-electron/main/index.js'),
      '--no-sandbox'
    ],
    env: {
      ...process.env,
      NODE_ENV: 'development'
    }
  });

  // 监听主进程日志
  electronApp.on('console', msg => {
    if (msg.text().includes('[Bangumi]') || msg.text().includes('cover')) {
      console.log('[Main]', msg.text());
    }
  });

  try {
    const window = await electronApp.firstWindow();
    await window.waitForLoadState('domcontentloaded');
    
    // 等待一段时间让封面加载
    await window.waitForTimeout(8000);
    
    // 获取页面上实际显示的图片 URL
    const imgSrcs = await window.evaluate(() => {
      const imgs = document.querySelectorAll('.anime-card .cover-image');
      return Array.from(imgs).slice(0, 3).map(img => ({
        src: img.src,
        naturalWidth: img.naturalWidth
      }));
    });
    
    console.log('\n[Test] Actual image elements on page:');
    for (const img of imgSrcs) {
      const isLarge = img.src?.includes('/l/');
      console.log(`  - ${isLarge ? '✅ /l/' : '⚠️ /c/'} width=${img.naturalWidth}px`);
      console.log(`    src: ${img.src}`);
    }
    
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
