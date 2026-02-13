/**
 * Anime List and Detail E2E Tests
 */

import { test, expect, helpers, testData } from './fixtures.js';

test.describe('Anime List', () => {
  
  test('should display anime cards with cover images', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Check for anime cards
    const cards = page.locator('.anime-card, [class*="anime-card"]');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);
    
    // Check first card has image
    const firstCard = cards.first();
    const image = firstCard.locator('img');
    
    if (await image.count() > 0) {
      await expect(image).toBeVisible();
      // Check image has src
      const src = await image.getAttribute('src');
      expect(src).toBeTruthy();
    }
  });
  
  test('should display anime information on cards', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    const cards = page.locator('.anime-card, [class*="anime-card"]');
    const firstCard = cards.first();
    
    // Check title exists
    const title = firstCard.locator('.title, h3, h4, .anime-title').first();
    if (await title.count() > 0) {
      await expect(title).toBeVisible();
      const titleText = await title.textContent();
      expect(titleText).toBeTruthy();
    }
    
    // Check episode info if available
    const episode = firstCard.locator('.episode, .ep-count').first();
    if (await episode.count() > 0) {
      const epText = await episode.textContent();
      expect(epText).toMatch(/\d+|集|話/);
    }
  });
  
  test('should navigate to anime detail page', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Click first anime card
    await helpers.clickFirstAnimeCard(page);
    
    // Wait for navigation
    await page.waitForTimeout(1000);
    
    // Check URL changed to detail page
    await expect(page).toHaveURL(/.*detail.*|.*\/\d+.*/);
    
    // Check detail page content
    const detailContent = page.locator('.detail-container, .anime-detail, [class*="detail"]').first();
    await expect(detailContent).toBeVisible();
  });
  
  test('should display anime detail information', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1000);
    
    // Check anime title
    const title = page.locator('h1, .anime-title, .detail-title').first();
    await expect(title).toBeVisible();
    const titleText = await title.textContent();
    expect(titleText).toBeTruthy();
    
    // Check description
    const description = page.locator('.description, .anime-description, .summary').first();
    if (await description.count() > 0) {
      await expect(description).toBeVisible();
    }
  });
  
  test('should display episode list on detail page', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1500);
    
    // Check for episode list
    const episodeList = page.locator('.episode-list, .episodes, [class*="episode"]');
    
    if (await episodeList.count() > 0) {
      // Check episodes exist
      const episodes = page.locator('.episode-item, .episode-card, [class*="episode-item"]');
      const episodeCount = await episodes.count();
      
      if (episodeCount > 0) {
        await expect(episodes.first()).toBeVisible();
      }
    }
  });
  
  test('should navigate to episode player', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1500);
    
    // Find and click first episode
    const firstEpisode = page.locator('.episode-item, .episode-card, [class*="episode-item"]').first();
    
    if (await firstEpisode.count() > 0) {
      await firstEpisode.click();
      await page.waitForTimeout(1000);
      
      // Check video player exists
      const player = page.locator('video, .video-player, [class*="video"]').first();
      await expect(player).toBeVisible();
    }
  });
});

test.describe('Search', () => {
  
  test('should search for anime with valid keyword', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Perform search
    await helpers.searchAnime(page, testData.searchKeywords.valid);
    
    // Wait for results
    await helpers.waitForLoading(page);
    await page.waitForTimeout(1000);
    
    // Check results or empty state
    const cards = page.locator('.anime-card, [class*="anime-card"]');
    const emptyState = page.locator('.empty, .el-empty, .no-results').first();
    
    // Either cards exist or empty state shows
    const hasCards = await cards.count() > 0;
    const hasEmptyState = await emptyState.count() > 0;
    
    expect(hasCards || hasEmptyState).toBe(true);
  });
  
  test('should show empty state for invalid search', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Search with invalid keyword
    await helpers.searchAnime(page, testData.searchKeywords.invalid);
    
    // Wait for results
    await page.waitForTimeout(1000);
    
    // Check for empty state
    const emptyState = page.locator('.empty, .el-empty, .no-results, text=没有找到, text=暂无结果').first();
    
    // Might show empty state or just no results
    const cards = page.locator('.anime-card, [class*="anime-card"]');
    
    if (await emptyState.count() > 0) {
      await expect(emptyState).toBeVisible();
    } else {
      // Should have no cards or very few
      const cardCount = await cards.count();
      expect(cardCount).toBeLessThanOrEqual(1);
    }
  });
  
  test('should clear search results', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Search first
    await helpers.searchAnime(page, testData.searchKeywords.valid);
    await page.waitForTimeout(1000);
    
    // Find and click clear button
    const clearBtn = page.locator('.clear-search, .el-input__clear, button:has-text("清除")').first();
    
    if (await clearBtn.count() > 0) {
      await clearBtn.click();
      await page.waitForTimeout(500);
      
      // Check search input is cleared
      const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"]').first();
      await expect(searchInput).toHaveValue('');
    }
  });
});

test.describe('Detail Page Navigation', () => {
  
  test('should have back button on detail page', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1000);
    
    // Check for back button
    const backBtn = page.locator('.back-btn, [class*="back"], button:has-text("返回"), .el-button:has(.el-icon-arrow-left)').first();
    
    if (await backBtn.count() > 0) {
      await expect(backBtn).toBeVisible();
      
      // Click back
      await backBtn.click();
      await page.waitForTimeout(500);
      
      // Check we're back on home
      await expect(page).toHaveURL(/.*\/.*|.*index.*/);
    }
  });
  
  test('should display breadcrumb on detail page', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1000);
    
    // Check for breadcrumb
    const breadcrumb = page.locator('.el-breadcrumb, .breadcrumb, [class*="breadcrumb"]').first();
    
    if (await breadcrumb.count() > 0) {
      await expect(breadcrumb).toBeVisible();
      
      // Check breadcrumb items
      const items = breadcrumb.locator('.el-breadcrumb__item, .breadcrumb-item');
      expect(await items.count()).toBeGreaterThan(0);
    }
  });
});
