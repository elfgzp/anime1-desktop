/**
 * Home Page and Navigation E2E Tests
 */

import { test, expect, helpers } from './fixtures.js';

test.describe('Home Page', () => {
  
  test('should display home page with anime list', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Anime1|番剧/);
    
    // Check main container exists
    await expect(page.locator('#app')).toBeVisible();
    
    // Wait for anime list to load
    await helpers.waitForLoading(page);
    
    // Check anime cards are displayed
    const cardCount = await helpers.getAnimeCardCount(page);
    expect(cardCount).toBeGreaterThan(0);
  });
  
  test('should display sidebar navigation', async ({ page }) => {
    // Check sidebar exists
    const sidebar = page.locator('.sidebar, .el-aside, nav').first();
    await expect(sidebar).toBeVisible();
    
    // Check navigation items
    const navItems = page.locator('.sidebar a, .el-menu-item, nav a');
    await expect(navItems.first()).toBeVisible();
  });
  
  test('should navigate to favorites page', async ({ page }) => {
    // Click on favorites link
    const favoritesLink = page.locator('a[href*="favorite"], .sidebar a:has-text("收藏"), nav a:has-text("收藏")').first();
    
    if (await favoritesLink.count() > 0) {
      await favoritesLink.click();
      await page.waitForTimeout(500);
      
      // Check URL changed
      await expect(page).toHaveURL(/.*favorite.*/);
      
      // Check favorites page content
      await expect(page.locator('text=收藏, text=我的收藏')).toBeVisible();
    }
  });
  
  test('should navigate to history page', async ({ page }) => {
    // Click on history link
    const historyLink = page.locator('a[href*="history"], .sidebar a:has-text("历史"), nav a:has-text("历史")').first();
    
    if (await historyLink.count() > 0) {
      await historyLink.click();
      await page.waitForTimeout(500);
      
      // Check URL changed
      await expect(page).toHaveURL(/.*history.*/);
      
      // Check history page content
      await expect(page.locator('text=播放历史, text=历史记录')).toBeVisible();
    }
  });
  
  test('should navigate to settings page', async ({ page }) => {
    // Click on settings link
    const settingsLink = page.locator('a[href*="setting"], .sidebar a:has-text("设置"), nav a:has-text("设置")').first();
    
    if (await settingsLink.count() > 0) {
      await settingsLink.click();
      await page.waitForTimeout(500);
      
      // Check URL changed
      await expect(page).toHaveURL(/.*setting.*/);
      
      // Check settings page content
      await expect(page.locator('text=设置, h1:has-text("设置")')).toBeVisible();
    }
  });
  
  test('should display pagination when available', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Check for pagination
    const pagination = page.locator('.el-pagination, .pagination').first();
    
    // Pagination might not exist if there's only one page
    if (await pagination.count() > 0) {
      await expect(pagination).toBeVisible();
    }
  });
  
  test('should have working search bar', async ({ page }) => {
    await helpers.waitForLoading(page);
    
    // Find search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], .search-input input').first();
    
    if (await searchInput.count() > 0) {
      await expect(searchInput).toBeVisible();
      
      // Type in search box
      await searchInput.fill('测试');
      await expect(searchInput).toHaveValue('测试');
    }
  });
});

test.describe('Theme Toggle', () => {
  
  test('should toggle between light and dark mode', async ({ page }) => {
    // Navigate to settings
    await helpers.navigateTo(page, '/#/settings');
    
    // Find theme selector
    const themeSelect = page.locator('.theme-select, select:has-option("暗黑"), select:has-option("深色")').first();
    
    if (await themeSelect.count() > 0) {
      // Get current theme
      const initialTheme = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
      });
      
      // Toggle theme
      await themeSelect.click();
      await page.waitForTimeout(200);
      
      // Select opposite theme
      const darkOption = page.locator('text=暗黑, text=深色, text=Dark').first();
      const lightOption = page.locator('text=普通, text=浅色, text=Light').first();
      
      if (initialTheme === 'dark' && await lightOption.count() > 0) {
        await lightOption.click();
      } else if (initialTheme === 'light' && await darkOption.count() > 0) {
        await darkOption.click();
      }
      
      await page.waitForTimeout(500);
      
      // Verify theme changed
      const newTheme = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
      });
      
      expect(newTheme).not.toBe(initialTheme);
    }
  });
});
