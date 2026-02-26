import { test, expect, chromium } from '@playwright/test';

/**
 * 视频播放端到端测试
 * 
 * 需要应用已启动并在开发模式下运行（npm run dev）
 * 或者通过 Electron 直接运行构建产物
 */
test('test detail page video playback', async () => {
  // 连接到已运行的 Electron 应用
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  
  // 找到主窗口（不是 DevTools）
  let targetPage = null;
  for (const context of browser.contexts()) {
    for (const page of context.pages()) {
      const url = page.url();
      if (url.includes('index.html') || url.includes('localhost')) {
        targetPage = page;
        break;
      }
    }
    if (targetPage) break;
  }
  
  if (!targetPage) {
    console.log('Main window not found');
    await browser.close();
    return;
  }
  
  const page = targetPage;
  
  // 回到首页
  await page.goto('file://' + process.cwd() + '/dist/index.html#/');
  await page.waitForTimeout(3000);
  
  // 点击第一个番剧卡片
  const firstCard = page.locator('.el-card').first();
  if (await firstCard.isVisible().catch(() => false)) {
    console.log('Clicking first anime card...');
    await firstCard.click();
    await page.waitForTimeout(3000);
    
    console.log('Detail page URL:', page.url());
    
    // 寻找并点击剧集按钮
    const selectors = [
      'text=/第\\d+集/',
      '.episode-item',
      'button:has-text("集")',
    ];
    
    let clicked = false;
    for (const selector of selectors) {
      const btn = page.locator(selector).first();
      if (await btn.isVisible().catch(() => false)) {
        console.log(`Clicking episode button: ${selector}`);
        await btn.click();
        clicked = true;
        break;
      }
    }
    
    // 如果没有找到，尝试点击数字按钮
    if (!clicked) {
      const buttons = await page.locator('button').all();
      for (const btn of buttons.slice(0, 10)) {
        const text = await btn.textContent().catch(() => '');
        if (/^\d+$/.test(text.trim())) {
          console.log(`Clicking numeric button: ${text}`);
          await btn.click();
          clicked = true;
          break;
        }
      }
    }
    
    if (clicked) {
      console.log('Waiting for video to load...');
      await page.waitForTimeout(8000);
      
      // 检查视频状态
      const videoInfo = await page.evaluate(() => {
        const video = document.querySelector('video');
        return video ? {
          src: video.src?.substring(0, 60),
          duration: video.duration,
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState
        } : null;
      });
      
      console.log('Video info:', JSON.stringify(videoInfo, null, 2));
      
      // 断言视频成功加载
      expect(videoInfo).not.toBeNull();
      expect(videoInfo?.duration).toBeGreaterThan(0);
      expect(videoInfo?.readyState).toBeGreaterThanOrEqual(2);
      
      console.log('✅ Video loaded successfully!');
    } else {
      console.log('❌ No episode button found');
    }
  } else {
    console.log('❌ No anime card found');
  }
  
  await browser.close();
});
