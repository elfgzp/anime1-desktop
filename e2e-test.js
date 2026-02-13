/**
 * E2E Test for Anime1 Desktop using Playwright
 * 
 * This script directly controls the Electron app for testing
 */

const { _electron: electron } = require('@playwright/test');
const path = require('path');

async function runTest() {
  console.log('🚀 Starting E2E test...');
  
  // Launch Electron app
  const electronApp = await electron.launch({
    args: ['.'],
    cwd: __dirname,
    env: {
      ...process.env,
      NODE_ENV: 'development'
    }
  });

  console.log('✅ Electron app launched');
  
  // Wait for main window
  const window = await electronApp.firstWindow();
  console.log('✅ Main window found');
  
  // Close DevTools if open
  await window.evaluate(() => {
    if (window.require) {
      const { ipcRenderer } = window.require('electron');
      // Can't directly close DevTools from renderer
    }
  }).catch(() => {});
  
  // Set viewport
  await window.setViewportSize({ width: 1280, height: 800 });
  
  // Wait for app to load
  await window.waitForLoadState('networkidle');
  console.log('✅ App loaded');
  
  // Listen to console messages
  const consoleLogs = [];
  window.on('console', msg => {
    consoleLogs.push({ type: msg.type(), text: msg.text() });
    console.log(`[${msg.type()}] ${msg.text().substring(0, 100)}`);
  });
  
  // Wait longer for data to load
  console.log('⏳ Waiting for data to load...');
  await window.waitForTimeout(12000);
  
  // Take screenshot of home page
  await window.screenshot({ path: '/tmp/anime1-home.png', fullPage: true });
  console.log('📸 Home page screenshot saved: /tmp/anime1-home.png');
  
  // Check if anime cards are loaded
  const animeCards = await window.locator('.anime-card').count();
  console.log(`📊 Found ${animeCards} anime cards`);
  
  // Also check for any error messages on page
  const pageText = await window.locator('body').textContent();
  if (pageText.includes('暂无番剧') || pageText.includes('网络错误')) {
    console.log('⚠️ Page shows no data message');
  }
  
  if (animeCards === 0) {
    console.log('❌ No anime cards found, checking for errors...');
    const consoleLogs = [];
    window.on('console', msg => consoleLogs.push(msg.text()));
    await window.waitForTimeout(2000);
    console.log('Console logs:', consoleLogs.slice(-10));
  }
  
  // Click first anime card
  const firstCard = window.locator('.anime-card').first();
  if (await firstCard.isVisible().catch(() => false)) {
    console.log('🖱️ Clicking first anime card...');
    await firstCard.click();
    
    // Wait for detail page
    await window.waitForTimeout(3000);
    
    // Take screenshot of detail page
    await window.screenshot({ path: '/tmp/anime1-detail.png' });
    console.log('📸 Detail page screenshot saved: /tmp/anime1-detail.png');
    
    // Check for episodes
    const episodeItems = await window.locator('.episode-item, [class*="episode"]').count();
    console.log(`📊 Found ${episodeItems} episode items`);
    
    // Click first episode if exists
    if (episodeItems > 0) {
      const firstEpisode = window.locator('.episode-item, [class*="episode"]').first();
      console.log('🖱️ Clicking first episode...');
      await firstEpisode.click();
      
      // Wait for video player
      await window.waitForTimeout(5000);
      
      // Take screenshot
      await window.screenshot({ path: '/tmp/anime1-video.png' });
      console.log('📸 Video page screenshot saved: /tmp/anime1-video.png');
      
      // Check for video element
      const videoElement = await window.locator('video').count();
      console.log(`📹 Found ${videoElement} video element(s)`);
      
      // Get video src
      if (videoElement > 0) {
        const videoSrc = await window.locator('video').getAttribute('src').catch(() => null);
        console.log(`🎬 Video src: ${videoSrc || 'No src found'}`);
      }
    }
  } else {
    console.log('❌ First anime card not visible');
  }
  
  // Get all console logs
  const logs = [];
  window.on('console', msg => {
    logs.push({ type: msg.type(), text: msg.text() });
  });
  
  await window.waitForTimeout(2000);
  
  // Filter important logs
  const errors = logs.filter(l => l.type === 'error');
  const warnings = logs.filter(l => l.type === 'warning');
  
  console.log('\n📋 Test Summary:');
  console.log(`- Console errors: ${errors.length}`);
  console.log(`- Console warnings: ${warnings.length}`);
  
  if (errors.length > 0) {
    console.log('\n❌ Errors found:');
    errors.forEach(e => console.log(`  - ${e.text.substring(0, 100)}`));
  }
  
  // Close app
  await electronApp.close();
  console.log('\n✅ Test completed');
}

runTest().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
