/**
 * Full E2E Test Suite for Anime1 Desktop
 * Tests all modules and records results
 */

const { chromium } = require('playwright');

// Test results storage
const testResults = {
  timestamp: new Date().toISOString(),
  modules: {}
};

async function runTest(name, testFn) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Testing: ${name}`);
  console.log('='.repeat(60));
  
  try {
    await testFn();
    testResults.modules[name] = { status: 'PASS', details: [] };
    console.log(`✅ ${name} - PASSED`);
    return true;
  } catch (error) {
    testResults.modules[name] = { status: 'FAIL', error: error.message, details: [] };
    console.log(`❌ ${name} - FAILED: ${error.message}`);
    return false;
  }
}

async function testHomePage(page) {
  console.log('\n📱 Testing Home Page...');
  
  // 1. Navigate to home
  await page.goto('http://localhost:3000/main_window/index.html#/');
  await page.waitForTimeout(8000);
  
  // 2. Check anime cards loaded
  const cards = await page.locator('.anime-card').all();
  console.log(`   Found ${cards.length} anime cards`);
  if (cards.length === 0) throw new Error('No anime cards found');
  
  // 3. Check covers loaded
  const cardsWithCovers = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.anime-card')).filter(card => {
      const img = card.querySelector('img');
      return img && img.complete && img.naturalWidth > 0;
    }).length;
  });
  console.log(`   Cards with covers: ${cardsWithCovers}/${cards.length}`);
  
  // 4. Test search
  const searchInput = await page.locator('input[placeholder*="搜索"]').first();
  if (await searchInput.isVisible().catch(() => false)) {
    await searchInput.fill('蘑菇');
    await page.waitForTimeout(2000);
    console.log('   Search input works');
  }
  
  // 5. Click first card
  await cards[0].click();
  await page.waitForTimeout(3000);
  
  const url = page.url();
  if (!url.includes('/anime/')) {
    throw new Error('Card click did not navigate to detail page');
  }
  console.log('   Card click navigation works');
  
  await page.screenshot({ path: 'screenshots/test-home.png' });
}

async function testDetailPage(page) {
  console.log('\n📄 Testing Detail Page...');
  
  // Should already be on detail page from home test
  // 1. Check sidebar cover
  const sidebarCover = await page.locator('.sidebar-cover-wrapper img').first();
  const hasSidebarCover = await sidebarCover.isVisible().catch(() => false);
  console.log(`   Sidebar cover: ${hasSidebarCover ? '✓' : '✗'}`);
  
  // 2. Check video player
  const videoPlayer = await page.locator('.video-js').first();
  const hasVideoPlayer = await videoPlayer.isVisible().catch(() => false);
  console.log(`   Video player: ${hasVideoPlayer ? '✓' : '✗'}`);
  
  // 3. Check episode buttons
  const episodeButtons = await page.locator('.episode-button, .episode-btn').all();
  console.log(`   Episode buttons: ${episodeButtons.length}`);
  
  // 4. Test favorite button
  const favButton = await page.locator('.favorite-btn, [class*="favorite"]').first();
  if (await favButton.isVisible().catch(() => false)) {
    await favButton.click();
    await page.waitForTimeout(1000);
    console.log('   Favorite button clicked');
  }
  
  // 5. Test back button
  const backButton = await page.locator('.back-btn').first();
  if (await backButton.isVisible().catch(() => false)) {
    await backButton.click();
    await page.waitForTimeout(3000);
    const url = page.url();
    console.log('   URL after back:', url);
    if (url.includes('/anime/')) {
      throw new Error('Back button did not navigate back');
    }
    console.log('   Back button works');
  }
  
  await page.screenshot({ path: 'screenshots/test-detail.png' });
}

async function testSidebarNavigation(page) {
  console.log('\n📑 Testing Sidebar Navigation...');
  
  // Get all sidebar menu items
  const sidebarItems = await page.locator('.el-aside .el-menu-item, .sidebar-item, nav a').all();
  console.log(`   Found ${sidebarItems.length} sidebar items`);
  
  // Test each menu item
  const menuNames = ['收藏', '历史', '下载', '设置'];
  for (const name of menuNames) {
    const item = await page.locator(`text=${name}`).first();
    if (await item.isVisible().catch(() => false)) {
      await item.click();
      await page.waitForTimeout(2000);
      console.log(`   Clicked ${name}`);
      await page.screenshot({ path: `screenshots/test-${name}.png` });
    }
  }
}

async function testVideoPlayback(page) {
  console.log('\n🎬 Testing Video Playback...');
  
  // Navigate to detail page
  await page.goto('http://localhost:3000/main_window/index.html#/');
  await page.waitForTimeout(5000);
  
  const cards = await page.locator('.anime-card').all();
  if (cards.length > 0) {
    await cards[0].click();
    await page.waitForTimeout(10000);
    
    // Check video status
    const videoStatus = await page.evaluate(() => {
      const video = document.querySelector('video');
      return {
        exists: !!video,
        src: video?.src,
        readyState: video?.readyState,
        error: video?.error?.message
      };
    });
    
    console.log('   Video status:', JSON.stringify(videoStatus, null, 2));
    
    if (!videoStatus.exists) {
      throw new Error('Video element not found');
    }
    
    if (videoStatus.error) {
      throw new Error(`Video error: ${videoStatus.error}`);
    }
  }
  
  await page.screenshot({ path: 'screenshots/test-video.png' });
}

async function main() {
  console.log('🚀 Starting Full E2E Test Suite...\n');
  
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const page = browser.contexts()[0].pages()[0];
  
  try {
    // Run all tests
    await runTest('Home Page', () => testHomePage(page));
    await runTest('Detail Page', () => testDetailPage(page));
    await runTest('Sidebar Navigation', () => testSidebarNavigation(page));
    await runTest('Video Playback', () => testVideoPlayback(page));
    
    // Print summary
    console.log('\n' + '='.repeat(60));
    console.log('Test Summary');
    console.log('='.repeat(60));
    
    let passed = 0;
    let failed = 0;
    
    for (const [name, result] of Object.entries(testResults.modules)) {
      if (result.status === 'PASS') {
        passed++;
        console.log(`✅ ${name}`);
      } else {
        failed++;
        console.log(`❌ ${name}: ${result.error}`);
      }
    }
    
    console.log(`\nTotal: ${passed} passed, ${failed} failed`);
    
    // Save report
    const fs = require('fs');
    fs.writeFileSync('test-report.json', JSON.stringify(testResults, null, 2));
    console.log('\nReport saved to test-report.json');
    
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
