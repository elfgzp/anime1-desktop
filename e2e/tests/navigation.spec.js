import { test, expect } from '@playwright/test';
import { SELECTORS } from '../fixtures/test-data.js';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the app to be ready
    await page.waitForSelector(SELECTORS.sidebar.container, { state: 'visible' });
  });

  test('should display sidebar with all menu items', async ({ page }) => {
    // Check sidebar is visible
    await expect(page.locator(SELECTORS.sidebar.container)).toBeVisible();
    
    // Check all menu items are present
    const menuItems = await page.$$(SELECTORS.sidebar.menuItems);
    expect(menuItems.length).toBeGreaterThanOrEqual(4);
    
    // Verify menu text content
    const sidebar = await page.locator(SELECTORS.sidebar.container);
    await expect(sidebar).toContainText('最新番剧');
    await expect(sidebar).toContainText('我的追番');
    await expect(sidebar).toContainText('观看历史');
    await expect(sidebar).toContainText('设置');
  });

  test('should navigate to Home page by default', async ({ page }) => {
    // Should show anime grid on home page
    await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
    
    // Should show search input
    await expect(page.locator(SELECTORS.home.searchInput)).toBeVisible();
  });

  test('should navigate to Favorites page', async ({ page }) => {
    // Click on favorites menu
    await page.click(SELECTORS.sidebar.favorites);
    
    // Wait for navigation
    await page.waitForURL('**/favorites');
    
    // Check favorites page is loaded
    await expect(page.locator(SELECTORS.favorites.container)).toBeVisible();
  });

  test('should navigate to History page', async ({ page }) => {
    // Click on history menu
    await page.click(SELECTORS.sidebar.history);
    
    // Wait for navigation
    await page.waitForURL('**/playback');
    
    // Check history page is loaded
    await expect(page.locator('text=观看历史')).toBeVisible();
  });

  test('should navigate to Settings page', async ({ page }) => {
    // Click on settings menu
    await page.click(SELECTORS.sidebar.settings);
    
    // Wait for navigation
    await page.waitForURL('**/settings');
    
    // Check settings page is loaded
    await expect(page.locator(SELECTORS.settings.container)).toBeVisible();
  });

  test('should toggle sidebar collapse', async ({ page }) => {
    // Find and click toggle button if exists
    const toggleButton = await page.$('.sidebar-toggle');
    if (toggleButton) {
      const sidebar = await page.$(SELECTORS.sidebar.container);
      const initialWidth = await sidebar.evaluate(el => el.offsetWidth);
      
      await toggleButton.click();
      
      // Wait for animation
      await page.waitForTimeout(300);
      
      const collapsedWidth = await sidebar.evaluate(el => el.offsetWidth);
      expect(collapsedWidth).toBeLessThan(initialWidth);
    }
  });
});
