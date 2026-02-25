// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright configuration for Anime1 Desktop E2E tests
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests',
  
  /* Run tests in files in parallel */
  fullyParallel: false,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
  
  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://localhost:5172',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video recording */
    video: 'on-first-retry',
    
    /* Default viewport */
    viewport: { width: 1280, height: 800 },
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
          ]
        }
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'cd .. && python -m src.app --port 5172 --flask-only',
    url: 'http://localhost:5172',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
  
  /* Global timeout */
  globalTimeout: 10 * 60 * 1000,
  
  /* Test timeout */
  timeout: 60 * 1000,
});
