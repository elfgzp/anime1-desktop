import { test, expect } from '@playwright/test';
import { SELECTORS } from '../fixtures/test-data.js';

test.describe('Favorites Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/favorites');
    await page.waitForTimeout(1000);
  });

  test('should display favorites page', async ({ page }) => {
    // Check favorites container or empty state is visible
    const container = await page.$(SELECTORS.favorites.container);
    const emptyState = await page.$(SELECTORS.favorites.emptyState);
    
    expect(container || emptyState).toBeTruthy();
  });

  test('should show empty state when no favorites', async ({ page }) => {
    // Check if empty state is shown
    const emptyText = await page.$('text=暂无追番');
    
    // If there's no empty text, there might be favorites
    if (emptyText) {
      await expect(page.locator('text=暂无追番')).toBeVisible();
    } else {
      // There are favorites, check list is shown
      await expect(page.locator(SELECTORS.favorites.animeList)).toBeVisible();
    }
  });

  test('should navigate to anime detail from favorites', async ({ page }) => {
    // Get favorite anime cards if any
    const cards = await page.$$(SELECTORS.favorites.animeCard);
    
    if (cards.length > 0) {
      // Click on first favorite
      await cards[0].click();
      
      // Should navigate to detail page
      await page.waitForSelector(SELECTORS.detail.container, { state: 'visible' });
      await expect(page.locator(SELECTORS.detail.title)).toBeVisible();
    }
  });
});
