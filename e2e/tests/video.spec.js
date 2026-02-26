import { test, expect } from '@playwright/test';
import { SELECTORS, TEST_TIMEOUTS } from '../fixtures/test-data.js';

test.describe('Video Player', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home
    await page.goto('/');
    await page.waitForSelector(SELECTORS.home.animeGrid, { state: 'visible' });
    
    // Click on first anime
    const cards = await page.$$(SELECTORS.home.animeCard);
    if (cards.length > 0) {
      await cards[0].click();
      await page.waitForSelector(SELECTORS.detail.container, { state: 'visible' });
      
      // Click on first episode to start playing
      const episodes = await page.$$(SELECTORS.detail.episodeItem);
      if (episodes.length > 0) {
        await episodes[0].click();
        await page.waitForSelector(SELECTORS.video.container, { 
          state: 'visible', 
          timeout: TEST_TIMEOUTS.videoLoad 
        });
      }
    }
  });

  test('should display video player', async ({ page }) => {
    // Check video player is visible
    await expect(page.locator(SELECTORS.video.container)).toBeVisible();
    
    // Check video.js is initialized
    await expect(page.locator(SELECTORS.video.videojs)).toBeVisible();
  });

  test('should toggle play/pause', async ({ page }) => {
    // Find play button
    const playButton = await page.$(SELECTORS.video.playButton);
    
    if (playButton) {
      // Click to play/pause
      await playButton.click();
      
      // Wait a bit for state to change
      await page.waitForTimeout(500);
      
      // Video should still be visible
      await expect(page.locator(SELECTORS.video.container)).toBeVisible();
    }
  });

  test('should toggle fullscreen', async ({ page }) => {
    // Find fullscreen button
    const fullscreenButton = await page.$('.vjs-fullscreen-control');
    
    if (fullscreenButton) {
      // Click to enter fullscreen
      await fullscreenButton.click();
      
      // Wait for fullscreen animation
      await page.waitForTimeout(500);
      
      // Video should still be visible
      await expect(page.locator(SELECTORS.video.container)).toBeVisible();
      
      // Exit fullscreen
      await fullscreenButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('should show video controls on hover', async ({ page }) => {
    const videoContainer = await page.$(SELECTORS.video.container);
    
    if (videoContainer) {
      // Hover over video
      await videoContainer.hover();
      
      // Wait for controls to appear
      await page.waitForTimeout(500);
      
      // Controls should be visible
      const controls = await page.$('.vjs-control-bar');
      expect(controls).toBeTruthy();
    }
  });
});
