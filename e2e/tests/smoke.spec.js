import { test, expect } from '@playwright/test';
import { AppPage } from '../helpers/AppPage.js';

/**
 * Smoke tests - Quick tests to verify basic functionality
 */
test.describe('Smoke Tests', () => {
  test('app loads successfully', async ({ page }) => {
    const app = new AppPage(page);
    await app.gotoHome();
    
    // Should show anime grid
    await app.expectAnimeGridVisible();
    
    // Should have anime cards
    await app.expectToHaveAnimeCards();
  });

  test('can navigate to all main pages', async ({ page }) => {
    const app = new AppPage(page);
    
    // Home
    await app.gotoHome();
    await expect(page).toHaveURL(/\/$/);
    
    // Favorites
    await app.gotoFavorites();
    await expect(page).toHaveURL(/\/favorites/);
    
    // Settings
    await app.gotoSettings();
    await expect(page).toHaveURL(/\/settings/);
  });

  test('can search for anime', async ({ page }) => {
    const app = new AppPage(page);
    await app.gotoHome();
    
    // Search for a common anime
    await app.searchAnime('鬼灭');
    
    // Should show results or empty state
    const hasCards = await page.$$(app.home.animeCard).then(cards => cards.length > 0);
    const hasEmpty = await page.$('text=暂无数据');
    
    expect(hasCards || hasEmpty).toBeTruthy();
  });

  test('can view anime detail', async ({ page }) => {
    const app = new AppPage(page);
    await app.gotoHome();
    
    // Click on first anime
    await app.clickAnimeCard(0);
    
    // Should show detail page
    await app.waitForDetailPage();
    
    // Should have title
    const title = await app.getAnimeTitle();
    expect(title).toBeTruthy();
  });
});
