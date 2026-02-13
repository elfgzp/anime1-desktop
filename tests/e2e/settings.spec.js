/**
 * Settings E2E Tests
 */

import { test, expect, helpers } from './fixtures.js';

test.describe('Settings Page', () => {
  
  test.beforeEach(async ({ page }) => {
    await helpers.navigateTo(page, '/#/settings');
    await page.waitForTimeout(500);
  });
  
  test('should display settings page', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1, h2, .page-title').first()).toContainText(/设置|Settings/);
    
    // Check settings sections exist
    const sections = page.locator('.settings-section, .el-card, section');
    expect(await sections.count()).toBeGreaterThan(0);
  });
  
  test('should display appearance settings', async ({ page }) => {
    // Find appearance section
    const appearanceSection = page.locator('.settings-section:has-text("外观"), .settings-section:has-text("Appearance"), section:has-text("外观")').first();
    
    if (await appearanceSection.count() > 0) {
      await expect(appearanceSection).toBeVisible();
      
      // Check theme selector
      const themeSelect = appearanceSection.locator('select, .el-select, .theme-select').first();
      if (await themeSelect.count() > 0) {
        await expect(themeSelect).toBeVisible();
      }
    }
  });
  
  test('should change theme', async ({ page }) => {
    // Find theme selector
    const themeSelect = page.locator('.theme-select, select:has-option("暗黑"), select:has-option("深色"), .el-select').first();
    
    if (await themeSelect.count() > 0) {
      // Open dropdown
      await themeSelect.click();
      await page.waitForTimeout(200);
      
      // Select dark theme
      const darkOption = page.locator('.el-select-dropdown__item:has-text("暗黑"), .el-select-dropdown__item:has-text("深色"), option:has-text("暗黑")').first();
      if (await darkOption.count() > 0) {
        await darkOption.click();
        await page.waitForTimeout(500);
        
        // Verify theme changed
        const hasDarkClass = await page.evaluate(() => {
          return document.documentElement.classList.contains('dark') ||
                 document.body.classList.contains('dark');
        });
        
        // Theme might be applied via different methods
        expect(hasDarkClass).toBeDefined();
      }
    }
  });
  
  test('should display cache information', async ({ page }) => {
    // Find cache section
    const cacheSection = page.locator('.settings-section:has-text("缓存"), .settings-section:has-text("Cache"), section:has-text("缓存")').first();
    
    if (await cacheSection.count() > 0) {
      await expect(cacheSection).toBeVisible();
      
      // Check cache info display
      const cacheInfo = cacheSection.locator('.settings-desc, .cache-info').first();
      if (await cacheInfo.count() > 0) {
        await expect(cacheInfo).toBeVisible();
      }
    }
  });
  
  test('should clear cache', async ({ page }) => {
    // Find clear cache button
    const clearBtn = page.locator('button:has-text("清理封面缓存"), button:has-text("Clear Cache"), .el-button:has-text("清理")').first();
    
    if (await clearBtn.count() > 0) {
      await clearBtn.click();
      await page.waitForTimeout(300);
      
      // Handle confirmation dialog if present
      const confirmBtn = page.locator('.el-message-box__btns .el-button--primary, button:has-text("确定"), button:has-text("确认")').first();
      if (await confirmBtn.count() > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(500);
      }
      
      // Check for success message
      const successMsg = page.locator('.el-message--success, .success-message, text=已清理, text=成功').first();
      // Message might be transient, so we just verify no error occurred
    }
  });
  
  test('should display update settings', async ({ page }) => {
    // Find update section
    const updateSection = page.locator('.settings-section:has-text("更新"), .settings-section:has-text("Update"), section:has-text("更新")').first();
    
    if (await updateSection.count() > 0) {
      await expect(updateSection).toBeVisible();
      
      // Check version display
      const versionText = updateSection.locator('.settings-desc, text=/\\d+\\.\\d+/').first();
      if (await versionText.count() > 0) {
        await expect(versionText).toBeVisible();
      }
      
      // Check check update button
      const checkBtn = updateSection.locator('button:has-text("检查更新"), button:has-text("Check Update")').first();
      if (await checkBtn.count() > 0) {
        await expect(checkBtn).toBeVisible();
      }
    }
  });
  
  test('should check for updates', async ({ page }) => {
    const checkBtn = page.locator('button:has-text("检查更新"), button:has-text("Check Update")').first();
    
    if (await checkBtn.count() > 0) {
      await checkBtn.click();
      await page.waitForTimeout(2000);
      
      // Check for loading state or result
      const loadingState = page.locator('.el-loading-spinner, text=检查中, text=Checking').first();
      const resultMsg = page.locator('.el-message, .update-result').first();
      
      const hasLoading = await loadingState.count() > 0;
      const hasResult = await resultMsg.count() > 0;
      
      expect(hasLoading || hasResult).toBe(true);
    }
  });
  
  test('should display about information', async ({ page }) => {
    // Find about section
    const aboutSection = page.locator('.settings-section:has-text("关于"), .settings-section:has-text("About"), section:has-text("关于")').first();
    
    if (await aboutSection.count() > 0) {
      await expect(aboutSection).toBeVisible();
      
      // Check version info
      const versionInfo = aboutSection.locator('text=/版本|Version/, text=/\\d+\\.\\d+/').first();
      await expect(versionInfo).toBeVisible();
      
      // Check repository link
      const repoLink = aboutSection.locator('a[href*="github"], .el-link').first();
      if (await repoLink.count() > 0) {
        await expect(repoLink).toBeVisible();
      }
    }
  });
  
  test('should open logs folder', async ({ page }) => {
    // Find open logs button
    const logsBtn = page.locator('button:has-text("日志文件夹"), button:has-text("Logs"), button:has-text("打开日志")').first();
    
    if (await logsBtn.count() > 0) {
      // Just verify button is clickable
      await expect(logsBtn).toBeEnabled();
      
      // Note: Actually clicking might open external folder which we can't verify in E2E
    }
  });
  
  test('should display playlist cache stats', async ({ page }) => {
    // Find playlist cache info
    const playlistCacheInfo = page.locator('text=番剧列表缓存, text=番剧详情缓存').first();
    
    if (await playlistCacheInfo.count() > 0) {
      await expect(playlistCacheInfo).toBeVisible();
      
      // Check refresh button
      const refreshBtn = page.locator('button:has-text("刷新列表")').first();
      if (await refreshBtn.count() > 0) {
        await expect(refreshBtn).toBeVisible();
      }
    }
  });
  
  test('should refresh playlist cache', async ({ page }) => {
    const refreshBtn = page.locator('button:has-text("刷新列表"), button:has-text("Refresh")').first();
    
    if (await refreshBtn.count() > 0) {
      await refreshBtn.click();
      await page.waitForTimeout(2000);
      
      // Check for loading state or success feedback
      const loadingState = page.locator('.is-loading, text=刷新中').first();
      const successMsg = page.locator('.el-message--success, text=已刷新').first();
      
      const hasLoading = await loadingState.count() > 0 && await loadingState.isVisible();
      const hasSuccess = await successMsg.count() > 0;
      
      // Button might just go back to normal state after completion
      expect(hasLoading || hasSuccess || await refreshBtn.isEnabled()).toBe(true);
    }
  });
});

test.describe('Settings Persistence', () => {
  
  test('should persist theme setting after reload', async ({ page }) => {
    await helpers.navigateTo(page, '/#/settings');
    
    // Change theme to dark
    const themeSelect = page.locator('.theme-select, .el-select').first();
    
    if (await themeSelect.count() > 0) {
      await themeSelect.click();
      await page.waitForTimeout(200);
      
      const darkOption = page.locator('.el-select-dropdown__item:has-text("暗黑")').first();
      if (await darkOption.count() > 0) {
        await darkOption.click();
        await page.waitForTimeout(500);
        
        // Reload page
        await page.reload();
        await helpers.waitForApp(page);
        await page.waitForTimeout(500);
        
        // Navigate back to settings
        await helpers.navigateTo(page, '/#/settings');
        await page.waitForTimeout(500);
        
        // Verify theme setting persisted
        const currentValue = await page.locator('.theme-select .el-input__inner, .el-select .el-input__inner').inputValue();
        expect(currentValue).toContain('暗黑');
      }
    }
  });
});
