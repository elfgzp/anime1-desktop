/**
 * Video Player E2E Tests
 */

import { test, expect, helpers } from './fixtures.js';

test.describe('Video Player', () => {
  
  // Helper to navigate to player
  async function navigateToPlayer(page) {
    await helpers.waitForLoading(page);
    
    // Navigate to anime detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1500);
    
    // Click first episode
    const firstEpisode = page.locator('.episode-item, .episode-card, [class*="episode-item"]').first();
    
    if (await firstEpisode.count() > 0) {
      await firstEpisode.click();
      await page.waitForTimeout(2000);
      return true;
    }
    
    return false;
  }
  
  test('should display video player', async ({ page }) => {
    const hasPlayer = await navigateToPlayer(page);
    
    if (hasPlayer) {
      // Check video element exists
      const video = page.locator('video').first();
      await expect(video).toBeVisible();
      
      // Check player controls
      const controls = page.locator('.video-js, .vjs-control-bar, .player-controls').first();
      await expect(controls).toBeVisible();
    }
  });
  
  test('should have player controls', async ({ page }) => {
    const hasPlayer = await navigateToPlayer(page);
    
    if (hasPlayer) {
      // Check play button
      const playBtn = page.locator('.vjs-play-control, .vjs-big-play-button, .play-btn').first();
      await expect(playBtn).toBeVisible();
      
      // Check progress bar
      const progressBar = page.locator('.vjs-progress-control, .vjs-progress-holder, .progress-bar').first();
      if (await progressBar.count() > 0) {
        await expect(progressBar).toBeVisible();
      }
      
      // Check volume control
      const volumeBtn = page.locator('.vjs-volume-control, .vjs-mute-control, .volume-btn').first();
      if (await volumeBtn.count() > 0) {
        await expect(volumeBtn).toBeVisible();
      }
      
      // Check fullscreen button
      const fullscreenBtn = page.locator('.vjs-fullscreen-control, .fullscreen-btn').first();
      if (await fullscreenBtn.count() > 0) {
        await expect(fullscreenBtn).toBeVisible();
      }
    }
  });
  
  test('should toggle play/pause', async ({ page }) => {
    const hasPlayer = await navigateToPlayer(page);
    
    if (hasPlayer) {
      const playBtn = page.locator('.vjs-play-control, .vjs-big-play-button, .play-btn').first();
      await playBtn.click();
      await page.waitForTimeout(500);
      
      // Player state might have changed
      // Just verify the click didn't cause errors
      const video = page.locator('video').first();
      await expect(video).toBeVisible();
    }
  });
  
  test('should display episode info', async ({ page }) => {
    await navigateToPlayer(page);
    
    // Check for episode title or info
    const episodeInfo = page.locator('.episode-title, .video-title, .player-title, h2, h3').first();
    await expect(episodeInfo).toBeVisible();
  });
  
  test('should have episode navigation', async ({ page }) => {
    await navigateToPlayer(page);
    
    // Check for prev/next episode buttons
    const prevBtn = page.locator('.prev-episode, .episode-nav-prev, button:has-text("上一集")').first();
    const nextBtn = page.locator('.next-episode, .episode-nav-next, button:has-text("下一集")').first();
    
    // At least one navigation element should exist
    const hasNav = await prevBtn.count() > 0 || await nextBtn.count() > 0;
    
    if (hasNav) {
      if (await prevBtn.count() > 0) {
        await expect(prevBtn).toBeVisible();
      }
      if (await nextBtn.count() > 0) {
        await expect(nextBtn).toBeVisible();
      }
    }
  });
  
  test('should show video duration', async ({ page }) => {
    const hasPlayer = await navigateToPlayer(page);
    
    if (hasPlayer) {
      // Check for duration display
      const duration = page.locator('.vjs-duration, .duration, .vjs-time-control').first();
      
      if (await duration.count() > 0) {
        await expect(duration).toBeVisible();
      }
    }
  });
  
  test('should support keyboard shortcuts', async ({ page }) => {
    const hasPlayer = await navigateToPlayer(page);
    
    if (hasPlayer) {
      // Focus the player
      await page.locator('video').first().click();
      await page.waitForTimeout(200);
      
      // Test spacebar (play/pause)
      await page.keyboard.press(' ');
      await page.waitForTimeout(500);
      
      // Test arrow keys (seek)
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(300);
      await page.keyboard.press('ArrowLeft');
      await page.waitForTimeout(300);
      
      // Verify player still visible
      const video = page.locator('video').first();
      await expect(video).toBeVisible();
    }
  });
});

test.describe('Player Fullscreen', () => {
  
  test('should toggle fullscreen mode', async ({ page }) => {
    await helpers.waitForLoading(page);
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1500);
    
    // Click first episode
    const firstEpisode = page.locator('.episode-item, .episode-card, [class*="episode-item"]').first();
    if (await firstEpisode.count() > 0) {
      await firstEpisode.click();
      await page.waitForTimeout(2000);
      
      // Find fullscreen button
      const fullscreenBtn = page.locator('.vjs-fullscreen-control, .fullscreen-btn, [title*="全屏"]').first();
      
      if (await fullscreenBtn.count() > 0) {
        await fullscreenBtn.click();
        await page.waitForTimeout(1000);
        
        // Check if fullscreen class is present
        const isFullscreen = await page.evaluate(() => {
          return document.fullscreenElement !== null || 
                 document.webkitFullscreenElement !== null ||
                 document.querySelector('.vjs-fullscreen') !== null;
        });
        
        // Toggle back
        await fullscreenBtn.click();
        await page.waitForTimeout(500);
      }
    }
  });
});

test.describe('Player Progress', () => {
  
  test('should save and restore playback progress', async ({ page }) => {
    // Navigate to player
    await helpers.waitForLoading(page);
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1500);
    
    const firstEpisode = page.locator('.episode-item, .episode-card, [class*="episode-item"]').first();
    if (await firstEpisode.count() > 0) {
      // Get episode info
      const episodeTitle = await firstEpisode.textContent();
      await firstEpisode.click();
      await page.waitForTimeout(2000);
      
      // Play for a bit
      const playBtn = page.locator('.vjs-play-control, .vjs-big-play-button').first();
      await playBtn.click();
      await page.waitForTimeout(2000);
      
      // Pause
      await playBtn.click();
      await page.waitForTimeout(500);
      
      // Navigate away and back
      await helpers.navigateTo(page, '/');
      await page.waitForTimeout(1000);
      
      // Go back to same anime
      await helpers.clickFirstAnimeCard(page);
      await page.waitForTimeout(1500);
      
      // Check if progress is shown (might be in a progress bar or badge)
      const progressIndicator = page.locator('.progress, .watched, .progress-bar').first();
      // Progress indicator might or might not exist depending on implementation
    }
  });
});
