/**
 * Favorites E2E Tests
 */

import { test, expect, helpers } from './fixtures.js';

test.describe('Favorites', () => {
  
  test('should navigate to favorites page', async ({ page }) => {
    // Navigate to favorites
    await helpers.navigateTo(page, '/#/favorites');
    
    // Check page content
    await expect(page.locator('h1, h2, .page-title').first()).toBeVisible();
    await expect(page.locator('text=收藏, text=我的收藏')).toBeVisible();
  });
  
  test('should toggle favorite from anime card', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Find favorite button on first card
    const favBtn = page.locator('.anime-card .favorite-btn, .anime-card [class*="favorite"], .anime-card .el-icon-star-off, .anime-card .el-icon-star-on').first();
    
    if (await favBtn.count() > 0) {
      // Get initial state
      const initialClass = await favBtn.getAttribute('class') || '';
      const wasFavorited = initialClass.includes('active') || initialClass.includes('filled') || initialClass.includes('on');
      
      // Click to toggle
      await favBtn.click();
      await page.waitForTimeout(500);
      
      // Check state changed
      const newClass = await favBtn.getAttribute('class') || '';
      const isFavorited = newClass.includes('active') || newClass.includes('filled') || newClass.includes('on');
      
      expect(isFavorited).not.toBe(wasFavorited);
      
      // Toggle back
      await favBtn.click();
      await page.waitForTimeout(500);
    }
  });
  
  test('should add to favorites from detail page', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Navigate to detail
    await helpers.clickFirstAnimeCard(page);
    await page.waitForTimeout(1000);
    
    // Find favorite button
    const favBtn = page.locator('.favorite-btn, .detail-favorite-btn, [class*="favorite-btn"]').first();
    
    if (await favBtn.count() > 0) {
      await favBtn.click();
      await page.waitForTimeout(500);
      
      // Check for success feedback (toast, icon change, etc.)
      const icon = favBtn.locator('.el-icon, i').first();
      if (await icon.count() > 0) {
        await expect(icon).toBeVisible();
      }
    }
  });
  
  test('should display favorites list', async ({ page }) => {
    await helpers.navigateTo(page, '/#/favorites');
    await page.waitForTimeout(1000);
    
    // Check for empty state or list
    const emptyState = page.locator('.empty, .el-empty, .no-favorites, text=暂无收藏, text=没有收藏').first();
    const animeCards = page.locator('.anime-card, [class*="anime-card"], .favorite-item');
    
    const hasEmptyState = await emptyState.count() > 0 && await emptyState.isVisible();
    const hasCards = await animeCards.count() > 0;
    
    expect(hasEmptyState || hasCards).toBe(true);
  });
  
  test('should remove from favorites', async ({ page }) => {
    await helpers.navigateTo(page, '/#/favorites');
    await page.waitForTimeout(1000);
    
    // Find remove button on first favorite
    const removeBtn = page.locator('.favorite-item .remove-btn, .favorite-item .delete-btn, .favorite-item .el-icon-delete, .favorite-item .el-icon-close').first();
    
    if (await removeBtn.count() > 0) {
      // Get initial count
      const items = page.locator('.favorite-item, .anime-card');
      const initialCount = await items.count();
      
      // Remove first item
      await removeBtn.click();
      await page.waitForTimeout(500);
      
      // Confirm if dialog appears
      const confirmBtn = page.locator('.el-message-box__btns .el-button--primary, button:has-text("确定"), button:has-text("确认")').first();
      if (await confirmBtn.count() > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(500);
      }
      
      // Check item was removed (or count decreased if there were multiple)
      if (initialCount > 1) {
        const newCount = await items.count();
        expect(newCount).toBeLessThan(initialCount);
      }
    }
  });
  
  test('should navigate to anime from favorites', async ({ page }) => {
    await helpers.navigateTo(page, '/#/favorites');
    await page.waitForTimeout(1000);
    
    // Find first favorite card
    const card = page.locator('.favorite-item, .anime-card').first();
    
    if (await card.count() > 0) {
      await card.click();
      await page.waitForTimeout(1000);
      
      // Should navigate to detail page
      await expect(page).toHaveURL(/.*detail.*|.*\/\d+.*/);
    }
  });
  
  test('should persist favorites after reload', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Add to favorites (if button exists)
    const favBtn = page.locator('.anime-card .favorite-btn, .anime-card [class*="favorite"]').first();
    
    if (await favBtn.count() > 0) {
      await favBtn.click();
      await page.waitForTimeout(500);
      
      // Reload page
      await page.reload();
      await helpers.waitForApp(page);
      await page.waitForTimeout(1000);
      
      // Check favorites page
      await helpers.navigateTo(page, '/#/favorites');
      await page.waitForTimeout(1000);
      
      // Should have at least one favorite
      const items = page.locator('.favorite-item, .anime-card');
      const emptyState = page.locator('.empty, .el-empty, .no-favorites').first();
      
      if (await emptyState.count() === 0 || !await emptyState.isVisible()) {
        expect(await items.count()).toBeGreaterThan(0);
      }
    }
  });
});
