/**
 * LLM Test Template - Anime1 Desktop E2E Testing
 * 
 * INSTRUCTIONS FOR LLM:
 * 1. Copy this file to create new tests
 * 2. Modify the TEST_CONFIG section below
 * 3. Run: node <test-file>.js (while app is running)
 * 
 * REQUIREMENTS:
 * - App must be running: npm start
 * - CDP port 9222 must be available
 * - Playwright must be installed
 */

const { chromium } = require('@playwright/test');

// ==================== TEST CONFIGURATION ====================
const TEST_CONFIG = {
  // Screenshot paths
  screenshots: {
    home: '/tmp/test-home.png',
    detail: '/tmp/test-detail.png',
    video: '/tmp/test-video.png',
  },
  
  // Timeouts (ms)
  timeouts: {
    pageLoad: 5000,
    dataFetch: 10000,
    videoLoad: 8000,
  },
  
  // Viewport
  viewport: { width: 1280, height: 800 },
  
  // Test flow
  actions: [
    // Example: Click first anime card
    { type: 'click', selector: '.anime-card', index: 0, waitAfter: 3000 },
    
    // Example: Click specific episode
    { type: 'click', selector: 'button:has-text("第07集")', waitAfter: 5000 },
    
    // Add more actions as needed...
  ],
  
  // Validation checks
  validations: [
    { type: 'elementExists', selector: '.anime-card', minCount: 1 },
    { type: 'consoleLog', shouldContain: '[API] getVideoInfo response' },
    // Add more validations...
  ]
};
// ==================== END CONFIGURATION ====================

async function runTest() {
  console.log('🚀 Starting LLM E2E Test...');
  console.log('📋 Config:', JSON.stringify(TEST_CONFIG.actions.length, null, 2));
  
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✅ Connected to Electron');
  
  const context = browser.contexts()[0];
  const pages = context.pages();
  
  // Find main window
  const mainPage = pages.find(p => p.url().includes('main_window'));
  if (!mainPage) {
    console.error('❌ Main window not found');
    console.log('Available pages:', pages.map(p => p.url()));
    await browser.close();
    return;
  }
  
  // Close DevTools
  const devTools = pages.find(p => p.url().startsWith('devtools://'));
  if (devTools) await devTools.close();
  
  // Setup
  await mainPage.setViewportSize(TEST_CONFIG.viewport);
  await mainPage.waitForLoadState('networkidle');
  
  // Collect console logs
  const consoleLogs = [];
  mainPage.on('console', msg => {
    const entry = { type: msg.type(), text: msg.text() };
    consoleLogs.push(entry);
    // Print important logs
    if (msg.text().includes('[API]') || msg.text().includes('error') || msg.text().includes('Error')) {
      console.log(`[${msg.type()}] ${msg.text().substring(0, 120)}`);
    }
  });
  
  // Initial screenshot
  await mainPage.screenshot({ path: TEST_CONFIG.screenshots.home });
  console.log('📸 Home screenshot saved');
  
  // Execute actions
  for (const action of TEST_CONFIG.actions) {
    try {
      switch (action.type) {
        case 'click':
          const locator = mainPage.locator(action.selector);
          const target = action.index !== undefined ? locator.nth(action.index) : locator.first();
          
          if (await target.isVisible().catch(() => false)) {
            console.log(`🖱️ Clicking: ${action.selector}`);
            await target.click();
            if (action.waitAfter) await mainPage.waitForTimeout(action.waitAfter);
          } else {
            console.log(`⚠️ Element not visible: ${action.selector}`);
          }
          break;
          
        case 'fill':
          await mainPage.fill(action.selector, action.value);
          console.log(`⌨️ Filled: ${action.selector}`);
          break;
          
        case 'screenshot':
          await mainPage.screenshot({ path: action.path || '/tmp/test-screenshot.png' });
          console.log(`📸 Screenshot: ${action.path}`);
          break;
          
        case 'wait':
          await mainPage.waitForTimeout(action.duration || 1000);
          break;
          
        default:
          console.log(`⚠️ Unknown action type: ${action.type}`);
      }
    } catch (err) {
      console.error(`❌ Action failed: ${action.type}`, err.message);
    }
  }
  
  // Run validations
  console.log('\n🔍 Running validations...');
  for (const validation of TEST_CONFIG.validations) {
    try {
      switch (validation.type) {
        case 'elementExists':
          const count = await mainPage.locator(validation.selector).count();
          const passed = count >= (validation.minCount || 1);
          console.log(`${passed ? '✅' : '❌'} ${validation.selector}: ${count} elements`);
          break;
          
        case 'consoleLog':
          const found = consoleLogs.some(log => log.text.includes(validation.shouldContain));
          console.log(`${found ? '✅' : '❌'} Console log contains: "${validation.shouldContain}"`);
          break;
          
        case 'pageUrl':
          const url = mainPage.url();
          const urlMatch = url.includes(validation.shouldContain);
          console.log(`${urlMatch ? '✅' : '❌'} URL contains: "${validation.shouldContain}"`);
          break;
      }
    } catch (err) {
      console.error(`❌ Validation error:`, err.message);
    }
  }
  
  // Summary
  console.log('\n📊 Test Summary:');
  console.log(`- Actions executed: ${TEST_CONFIG.actions.length}`);
  console.log(`- Validations run: ${TEST_CONFIG.validations.length}`);
  console.log(`- Console logs captured: ${consoleLogs.length}`);
  console.log(`- Errors: ${consoleLogs.filter(l => l.type === 'error').length}`);
  
  // Error analysis
  const errors = consoleLogs.filter(l => l.type === 'error');
  if (errors.length > 0) {
    console.log('\n❌ Console Errors:');
    errors.slice(0, 5).forEach(e => console.log(`  - ${e.text.substring(0, 100)}`));
  }
  
  await browser.close();
  console.log('\n✅ Test completed');
}

runTest().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
