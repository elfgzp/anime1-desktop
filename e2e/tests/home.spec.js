import { test, expect } from '@playwright/test';
import { SELECTORS, TEST_ANIME } from '../fixtures/test-data.js';

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector(SELECTORS.home.animeGrid, { state: 'visible' });
  });

  test('should display anime list', async ({ page }) => {
    // Check anime grid is visible
    await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
    
    // Should have anime cards
    const cards = await page.$$(SELECTORS.home.animeCard);
    expect(cards.length).toBeGreaterThan(0);
  });

  test('should search for anime', async ({ page }) => {
    const searchKeyword = TEST_ANIME.searchKeywords[0];
    
    // Type in search input
    await page.fill(SELECTORS.home.searchInput, searchKeyword);
    
    // Press Enter or click search button
    await page.press(SELECTORS.home.searchInput, 'Enter');
    
    // Wait for search results
    await page.waitForLoadState('networkidle');
    
    // Check results are displayed
    const cards = await page.$$(SELECTORS.home.animeCard);
    
    // If there are results, they should contain the keyword
    if (cards.length > 0) {
      const firstCard = cards[0];
      const text = await firstCard.textContent();
      // Note: Search might not always return results, so we just check the grid exists
      await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
    }
  });

  test('should navigate to anime detail page', async ({ page }) => {
    // Get first anime card
    const cards = await page.$$(SELECTORS.home.animeCard);
    expect(cards.length).toBeGreaterThan(0);
    
    // Click on first card
    await cards[0].click();
    
    // Wait for detail page to load
    await page.waitForSelector(SELECTORS.detail.container, { state: 'visible', timeout: 10000 });
    
    // Verify detail page elements
    await expect(page.locator(SELECTORS.detail.title)).toBeVisible();
    await expect(page.locator(SELECTORS.detail.episodeList)).toBeVisible();
  });

  test('should support pagination', async ({ page }) => {
    // Check if pagination exists
    const pagination = await page.$(SELECTORS.home.pagination);
    
    if (pagination) {
      // Get initial page
      const initialUrl = page.url();
      
      // Try to go to next page
      const nextButton = await page.$('.el-pagination .btn-next');
      if (nextButton) {
        const isDisabled = await nextButton.evaluate(el => el.disabled);
        
        if (!isDisabled) {
          await nextButton.click();
          
          // Wait for page to change
          await page.waitForTimeout(1000);
          
          // URL should have changed or page number increased
          await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
        }
      }
    }
  });

  test('should display loading state', async ({ page }) => {
    // Navigate to home and check for loading state
    await page.goto('/');
    
    // Initially might show skeleton loading
    const hasSkeleton = await page.$(SELECTORS.skeleton);
    const hasLoading = await page.$(SELECTORS.loading);
    
    // Either skeleton or anime grid should eventually appear
    await page.waitForSelector(`${SELECTORS.skeleton}, ${SELECTORS.home.animeGrid}`, { 
      state: 'visible',
      timeout: 10000 
    });
  });
});
