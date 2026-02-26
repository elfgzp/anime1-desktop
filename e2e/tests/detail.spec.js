import { test, expect } from '@playwright/test';
import { SELECTORS } from '../fixtures/test-data.js';

test.describe('Anime Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home first
    await page.goto('/');
    await page.waitForSelector(SELECTORS.home.animeGrid, { state: 'visible' });
    
    // Click on first anime to go to detail page
    const cards = await page.$$(SELECTORS.home.animeCard);
    if (cards.length > 0) {
      await cards[0].click();
      await page.waitForSelector(SELECTORS.detail.container, { state: 'visible' });
    }
  });

  test('should display anime details', async ({ page }) => {
    // Check title is displayed
    await expect(page.locator(SELECTORS.detail.title)).toBeVisible();
    
    // Check cover image
    await expect(page.locator(SELECTORS.detail.cover)).toBeVisible();
    
    // Check episode list
    await expect(page.locator(SELECTORS.detail.episodeList)).toBeVisible();
  });

  test('should display episode list', async ({ page }) => {
    // Get all episode items
    const episodes = await page.$$(SELECTORS.detail.episodeItem);
    
    // There should be at least one episode or an empty state
    if (episodes.length === 0) {
      // Check for empty state message
      const emptyText = await page.$('text=暂无剧集');
      expect(emptyText || episodes.length > 0).toBeTruthy();
    } else {
      expect(episodes.length).toBeGreaterThan(0);
    }
  });

  test('should toggle favorite status', async ({ page }) => {
    // Find favorite button
    const favoriteButton = await page.$(SELECTORS.detail.favoriteButton);
    
    if (favoriteButton) {
      // Get initial state
      const initialText = await favoriteButton.textContent();
      
      // Click to toggle
      await favoriteButton.click();
      
      // Wait for state change (API call)
      await page.waitForTimeout(1000);
      
      // Check toast message appears
      await expect(page.locator(SELECTORS.toast)).toBeVisible();
    }
  });

  test('should navigate back to home', async ({ page }) => {
    // Click back button
    const backButton = await page.$(SELECTORS.detail.backButton);
    if (backButton) {
      await backButton.click();
      
      // Should return to home page
      await page.waitForSelector(SELECTORS.home.animeGrid, { state: 'visible' });
      await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
    }
  });

  test('should play video when clicking episode', async ({ page }) => {
    // Get first episode
    const episodes = await page.$$(SELECTORS.detail.episodeItem);
    
    if (episodes.length > 0) {
      // Click on first episode
      await episodes[0].click();
      
      // Wait for video player to appear
      const videoPlayer = await page.waitForSelector(SELECTORS.video.container, { 
        state: 'visible', 
        timeout: 15000 
      });
      
      expect(videoPlayer).toBeTruthy();
    }
  });
});
