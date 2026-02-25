// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright configuration for Desktop App E2E tests
 * Tests the actual pywebview desktop application
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests-desktop',
  
  /* Run tests in files in parallel */
  fullyParallel: false,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI */
  workers: 1,
  
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report-desktop' }],
    ['list'],
    ['junit', { outputFile: 'test-results/desktop-junit.xml' }]
  ],
  
  /* Shared settings for all the projects below */
  use: {
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video recording */
    video: 'on-first-retry',
    
    /* Default viewport - matches typical desktop window */
    viewport: { width: 1280, height: 800 },
    
    /* Action timeout */
    actionTimeout: 15000,
    
    /* Navigation timeout */
    navigationTimeout: 30000,
  },

  /* Configure projects for desktop testing */
  projects: [
    {
      name: 'desktop-chromium',
      use: { 
        browserName: 'chromium',
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-dev-shm-usage',
            '--no-sandbox',
          ],
        },
        // Connect to the desktop app via CDP
        connectOptions: {
          wsEndpoint: process.env.CDP_WS_URL || 'ws://localhost:9222/devtools/browser',
        },
      },
    },
  ],

  /* Global setup - can be used to start the app */
  // globalSetup: require.resolve('./global-setup'),
  
  /* Global teardown */
  // globalTeardown: require.resolve('./global-teardown'),
  
  /* Global timeout */
  globalTimeout: 10 * 60 * 1000,
  
  /* Test timeout */
  timeout: 120 * 1000,
  
  /* Expect timeout */
  expect: {
    timeout: 15000,
  },
});
