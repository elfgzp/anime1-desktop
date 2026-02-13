/**
 * E2E Test for Anime1 Desktop using Playwright + CDP
 * Connects to running Electron instance
 */

const { chromium } = require('@playwright/test');

async function runTest() {
  console.log('🚀 Starting E2E test via CDP...');
  
  // Connect to Electron via CDP
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✅ Connected to Electron');
  
  // Get contexts and pages
  const context = browser.contexts()[0];
  const pages = context.pages();
  
  // Find main window
  const mainPage = pages.find(p => p.url().includes('main_window'));
  if (!mainPage) {
    console.log('❌ Main window not found. Available pages:');
    pages.forEach(p => console.log(`  - ${p.url()}`));
    await browser.close();
    return;
  }
  
  console.log('✅ Found main window');
  
  // Close DevTools if present
  const devToolsPage = pages.find(p => p.url().startsWith('devtools://'));
  if (devToolsPage) {
    await devToolsPage.close();
    console.log('✅ Closed DevTools');
  }
  
  // Set viewport
  await mainPage.setViewportSize({ width: 1280, height: 800 });
  
  // Listen to console
  mainPage.on('console', msg => {
    const text = msg.text();
    if (text.includes('Video') || text.includes('video') || text.includes('error') || text.includes('Error')) {
      console.log(`[${msg.type()}] ${text.substring(0, 150)}`);
    }
  });
  
  // Wait for page to be ready
  await mainPage.waitForLoadState('networkidle');
  await mainPage.waitForTimeout(3000);
  
  // Take screenshot
  await mainPage.screenshot({ path: '/tmp/anime1-home.png' });
  console.log('📸 Home page screenshot saved');
  
  // Check for anime cards
  const cards = await mainPage.locator('.anime-card').count();
  console.log(`📊 Found ${cards} anime cards`);
  
  if (cards === 0) {
    console.log('⚠️ No cards found, waiting longer...');
    await mainPage.waitForTimeout(5000);
    const cards2 = await mainPage.locator('.anime-card').count();
    console.log(`📊 After wait: ${cards2} anime cards`);
  }
  
  // Click first card
  const firstCard = mainPage.locator('.anime-card').first();
  if (await firstCard.isVisible().catch(() => false)) {
    console.log('🖱️ Clicking first anime card...');
    await firstCard.click();
    
    await mainPage.waitForTimeout(3000);
    await mainPage.screenshot({ path: '/tmp/anime1-detail.png' });
    console.log('📸 Detail page screenshot saved');
    
    // Check page content
    const title = await mainPage.locator('h1, h2').first().textContent().catch(() => '');
    console.log(`📝 Page title: ${title.substring(0, 50)}`);
    
    // Click first episode
    const episodeBtn = mainPage.locator('button:has-text("第"), .episode-item, [class*="episode"]').first();
    const episodeCount = await mainPage.locator('button:has-text("第"), .episode-item').count();
    console.log(`📺 Found ${episodeCount} episode buttons`);
    
    if (await episodeBtn.isVisible().catch(() => false)) {
      console.log('🖱️ Clicking first episode...');
      await episodeBtn.click();
      
      await mainPage.waitForTimeout(5000);
      await mainPage.screenshot({ path: '/tmp/anime1-video.png' });
      console.log('📸 Video page screenshot saved');
      
      // Check video
      const video = await mainPage.locator('video').count();
      console.log(`🎬 Video elements: ${video}`);
      
      if (video > 0) {
        const videoSrc = await mainPage.locator('video').getAttribute('src').catch(() => null);
        console.log(`✅ Video src: ${videoSrc ? 'Found' : 'Not found'}`);
        
        // Check for error messages
        const errorText = await mainPage.locator('.video-error, [class*="error"]').textContent().catch(() => '');
        if (errorText) {
          console.log(`⚠️ Video error: ${errorText.substring(0, 100)}`);
        }
      }
    }
  } else {
    console.log('❌ No anime card visible');
    // Take screenshot to debug
    await mainPage.screenshot({ path: '/tmp/anime1-debug.png' });
  }
  
  await browser.close();
  console.log('\n✅ Test completed');
}

runTest().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
