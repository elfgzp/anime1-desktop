/**
 * E2E Test Fixtures and Helpers
 */

import { test as base, expect } from '@playwright/test';

/**
 * Test data fixtures
 */
export const testData = {
  // Sample anime titles for testing
  animeTitles: [
    '鬼灭之刃',
    '咒术回战',
    '进击的巨人',
  ],
  
  // Test search keywords
  searchKeywords: {
    valid: '鬼灭',
    invalid: 'xyz123notfound',
  },
  
  // Test timeouts
  timeouts: {
    navigation: 10000,
    animation: 500,
    api: 15000,
  },
};

/**
 * Helper functions for E2E tests
 */
export const helpers = {
  /**
   * Wait for app to be ready
   */
  async waitForApp(page) {
    // Wait for the app to load (Vue mounted)
    await page.waitForSelector('#app', { timeout: testData.timeouts.navigation });
    // Wait for initial data to load
    await page.waitForTimeout(1000);
  },
  
  /**
   * Navigate to a route
   */
  async navigateTo(page, route) {
    await page.goto(route);
    await this.waitForApp(page);
  },
  
  /**
   * Wait for loading to complete
   */
  async waitForLoading(page) {
    // Wait for loading spinners to disappear
    await page.waitForFunction(() => {
      const spinners = document.querySelectorAll('.el-loading-spinner, .loading-spinner, .is-loading');
      return spinners.length === 0;
    }, { timeout: testData.timeouts.api });
  },
  
  /**
   * Check if element exists
   */
  async elementExists(page, selector) {
    return await page.locator(selector).count() > 0;
  },
  
  /**
   * Get anime card count
   */
  async getAnimeCardCount(page) {
    return await page.locator('.anime-card, [class*="anime-card"]').count();
  },
  
  /**
   * Click first anime card
   */
  async clickFirstAnimeCard(page) {
    const card = page.locator('.anime-card, [class*="anime-card"]').first();
    await card.waitFor({ state: 'visible' });
    await card.click();
  },
  
  /**
   * Search for anime
   */
  async searchAnime(page, keyword) {
    const searchInput = page.locator('input[placeholder*="搜索"], .search-input input').first();
    await searchInput.fill(keyword);
    await searchInput.press('Enter');
    await page.waitForTimeout(testData.timeouts.animation);
  },
  
  /**
   * Toggle favorite
   */
  async toggleFavorite(page) {
    const favBtn = page.locator('.favorite-btn, [class*="favorite"]').first();
    await favBtn.click();
    await page.waitForTimeout(testData.timeouts.animation);
  },
  
  /**
   * Take screenshot with timestamp
   */
  async takeScreenshot(page, name) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({ 
      path: `tests/e2e/screenshots/${name}-${timestamp}.png`,
      fullPage: true 
    });
  },
};

/**
 * Custom test with fixtures
 */
export const test = base.extend({
  /**
   * Navigate to home page before each test
   */
  page: async ({ page }, use) => {
    await helpers.navigateTo(page, '/');
    await use(page);
  },
  
  /**
   * Test data fixture
   */
  testData: async ({}, use) => {
    await use(testData);
  },
  
  /**
   * Helpers fixture
   */
  helpers: async ({}, use) => {
    await use(helpers);
  },
});

export { expect };
