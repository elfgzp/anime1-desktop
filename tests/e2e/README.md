# E2E Tests with Playwright

This directory contains End-to-End (E2E) tests using Playwright for the Anime1 Desktop application.

## Test Structure

```
tests/e2e/
├── fixtures.js          # Test fixtures and helper functions
├── home.spec.js         # Home page and navigation tests
├── anime.spec.js        # Anime list and detail tests
├── player.spec.js       # Video player tests
├── favorites.spec.js    # Favorites functionality tests
├── settings.spec.js     # Settings page tests
└── README.md           # This file
```

## Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI mode
npm run test:e2e:ui

# Run specific test file
npx playwright test tests/e2e/home.spec.js

# Run tests in headed mode (visible browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Test Coverage

### Home Page (`home.spec.js`)
- Display home page with anime list
- Sidebar navigation
- Navigate to favorites/history/settings
- Theme toggle

### Anime List & Detail (`anime.spec.js`)
- Display anime cards with covers
- Navigate to detail page
- Display episode list
- Search functionality
- Detail page navigation

### Video Player (`player.spec.js`)
- Display video player
- Player controls (play/pause, volume, fullscreen)
- Keyboard shortcuts
- Episode navigation
- Progress tracking

### Favorites (`favorites.spec.js`)
- Navigate to favorites page
- Toggle favorite from card/detail
- Remove from favorites
- Persistence after reload

### Settings (`settings.spec.js`)
- Display settings page
- Theme change
- Cache management
- Update check
- Settings persistence

## Writing Tests

### Basic Test Structure

```javascript
import { test, expect, helpers } from './fixtures.js';

test.describe('Feature Name', () => {
  
  test('should do something', async ({ page }) => {
    // Navigate and wait for app
    await helpers.waitForLoading(page);
    
    // Perform actions
    await page.click('.some-button');
    
    // Assert results
    await expect(page.locator('.result')).toBeVisible();
  });
});
```

### Available Helpers

- `helpers.waitForApp(page)` - Wait for app to load
- `helpers.waitForLoading(page)` - Wait for loading to complete
- `helpers.clickFirstAnimeCard(page)` - Click first anime card
- `helpers.searchAnime(page, keyword)` - Search for anime
- `helpers.takeScreenshot(page, name)` - Take screenshot

### Test Data

```javascript
import { testData } from './fixtures.js';

// Available data
testData.animeTitles      // Sample anime titles
testData.searchKeywords   // Search test keywords
testData.timeouts         // Timeout values
```

## Best Practices

1. **Use fixtures**: Import from `fixtures.js` for consistency
2. **Wait for loading**: Always use `waitForLoading()` before assertions
3. **Handle optional elements**: Check element existence before interacting
4. **Use test data**: Use `testData` for consistent test inputs
5. **Clean state**: Don't assume previous test state
6. **Screenshots**: Take screenshots on failure for debugging

## Configuration

See `playwright.config.js` for test configuration:
- Base URL
- Browsers
- Timeouts
- Reporters

## CI/CD Integration

Tests can be run in CI with:

```bash
# Run in CI mode (no watch, fail on test.only)
CI=true npm run test:e2e
```

## Troubleshooting

### Tests failing due to timing
Increase timeout or add explicit waits:
```javascript
await page.waitForTimeout(1000);
```

### Element not found
Use flexible selectors and check existence:
```javascript
const element = page.locator('.class, [attr="value"]').first();
if (await element.count() > 0) {
  await element.click();
}
```

### Flaky tests
- Use `test.only` to isolate
- Add `await page.waitForLoadState('networkidle')`
- Increase `expect` timeout in config

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Selectors](https://playwright.dev/docs/selectors)
