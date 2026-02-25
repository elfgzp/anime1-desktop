/**
 * Page Object Model for Anime1 Desktop Application
 * Provides high-level abstractions for common app interactions
 */
export class AppPage {
  constructor(page) {
    this.page = page;
    
    // Selectors
    this.sidebar = {
      container: '.sidebar',
      homeMenu: '[data-testid="menu-home"]',
      favoritesMenu: '[data-testid="menu-favorites"]',
      historyMenu: '[data-testid="menu-history"]',
      settingsMenu: '[data-testid="menu-settings"]',
      autoDownloadMenu: '[data-testid="menu-auto-download"]',
      toggleButton: '.sidebar-toggle',
    };
    
    this.home = {
      searchInput: '[data-testid="search-input"]',
      searchButton: '[data-testid="search-button"]',
      animeGrid: '[data-testid="anime-grid"]',
      animeCard: '[data-testid="anime-card"]',
      pagination: '.el-pagination',
    };
    
    this.detail = {
      container: '[data-testid="anime-detail"]',
      title: '[data-testid="anime-title"]',
      episodeList: '[data-testid="episode-list"]',
      episodeItem: '[data-testid="episode-item"]',
      playButton: '[data-testid="play-button"]',
      favoriteButton: '[data-testid="favorite-button"]',
      videoPlayer: '[data-testid="video-player"]',
      backButton: '[data-testid="back-button"]',
    };
    
    this.video = {
      container: '.video-js',
      playButton: '.vjs-play-control',
      fullscreenButton: '.vjs-fullscreen-control',
      progressBar: '.vjs-progress-control',
      currentTime: '.vjs-current-time',
      duration: '.vjs-duration',
    };
    
    this.favorites = {
      container: '[data-testid="favorites-page"]',
      emptyState: '[data-testid="empty-favorites"]',
      animeCard: '[data-testid="favorite-anime-card"]',
      removeButton: '[data-testid="remove-favorite"]',
    };
    
    this.settings = {
      container: '[data-testid="settings-page"]',
      themeSelector: '[data-testid="theme-selector"]',
      checkUpdateButton: '[data-testid="check-update"]',
      clearCacheButton: '[data-testid="clear-cache"]',
      cacheInfo: '[data-testid="cache-info"]',
    };
  }

  // Navigation
  async gotoHome() {
    await this.page.goto('/');
    await this.waitForHomePage();
  }

  async gotoFavorites() {
    await this.page.click(this.sidebar.favoritesMenu);
    await this.waitForFavoritesPage();
  }

  async gotoSettings() {
    await this.page.click(this.sidebar.settingsMenu);
    await this.waitForSettingsPage();
  }

  // Wait helpers
  async waitForHomePage() {
    await this.page.waitForSelector(this.home.animeGrid, { state: 'visible', timeout: 10000 });
  }

  async waitForDetailPage() {
    await this.page.waitForSelector(this.detail.container, { state: 'visible', timeout: 10000 });
  }

  async waitForFavoritesPage() {
    await this.page.waitForSelector(this.favorites.container, { state: 'visible', timeout: 10000 });
  }

  async waitForSettingsPage() {
    await this.page.waitForSelector(this.settings.container, { state: 'visible', timeout: 10000 });
  }

  async waitForVideoPlayer() {
    await this.page.waitForSelector(this.video.container, { state: 'visible', timeout: 15000 });
  }

  // Home page actions
  async searchAnime(keyword) {
    await this.page.fill(this.home.searchInput, keyword);
    await this.page.click(this.home.searchButton);
    await this.page.waitForLoadState('networkidle');
  }

  async getAnimeCards() {
    return await this.page.$$(this.home.animeCard);
  }

  async clickAnimeCard(index = 0) {
    const cards = await this.getAnimeCards();
    if (cards[index]) {
      await cards[index].click();
      await this.waitForDetailPage();
    }
  }

  // Detail page actions
  async getAnimeTitle() {
    return await this.page.textContent(this.detail.title);
  }

  async playEpisode(index = 0) {
    const episodes = await this.page.$$(this.detail.episodeItem);
    if (episodes[index]) {
      await episodes[index].click();
      await this.waitForVideoPlayer();
    }
  }

  async toggleFavorite() {
    await this.page.click(this.detail.favoriteButton);
  }

  async goBack() {
    await this.page.click(this.detail.backButton);
    await this.waitForHomePage();
  }

  // Video player actions
  async togglePlay() {
    await this.page.click(this.video.playButton);
  }

  async toggleFullscreen() {
    await this.page.click(this.video.fullscreenButton);
  }

  async seekTo(percentage) {
    const progressBar = await this.page.$(this.video.progressBar);
    const box = await progressBar.boundingBox();
    const x = box.x + (box.width * percentage);
    const y = box.y + box.height / 2;
    await this.page.mouse.click(x, y);
  }

  // Settings actions
  async changeTheme(theme) {
    await this.page.selectOption(this.settings.themeSelector, theme);
  }

  async clearCache() {
    await this.page.click(this.settings.clearCacheButton);
    // Wait for confirmation dialog
    await this.page.waitForSelector('.el-message-box', { state: 'visible' });
    await this.page.click('.el-message-box .el-button--primary');
  }

  async checkForUpdates() {
    await this.page.click(this.settings.checkUpdateButton);
  }

  // Sidebar actions
  async toggleSidebar() {
    await this.page.click(this.sidebar.toggleButton);
  }

  async isSidebarCollapsed() {
    const sidebar = await this.page.$(this.sidebar.container);
    const className = await sidebar.getAttribute('class');
    return className.includes('collapsed');
  }

  // Assertions helpers
  async expectAnimeGridVisible() {
    await this.page.waitForSelector(this.home.animeGrid, { state: 'visible' });
  }

  async expectVideoPlayerVisible() {
    await this.page.waitForSelector(this.video.container, { state: 'visible' });
  }

  async expectToHaveAnimeCards() {
    const cards = await this.getAnimeCards();
    if (cards.length === 0) {
      throw new Error('Expected anime cards to be present but found none');
    }
  }
}
