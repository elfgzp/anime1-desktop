# Anime1 Desktop E2E Tests

使用 Playwright 进行端到端测试。

## 安装

```bash
cd e2e
npm install
npx playwright install chromium
```

## 运行测试

```bash
# 运行所有测试
npm test

# 运行测试（带 UI）
npm run test:ui

# 调试模式
npm run test:debug

# 有头模式（可以看到浏览器）
npm run test:headed

# 查看报告
npm run report
```

## 测试结构

```
e2e/
├── tests/
│   ├── navigation.spec.js    # 导航测试
│   ├── home.spec.js          # 首页测试
│   ├── detail.spec.js        # 详情页测试
│   ├── video.spec.js         # 视频播放测试
│   ├── favorites.spec.js     # 收藏页面测试
│   └── settings.spec.js      # 设置页面测试
├── helpers/
│   └── AppPage.js            # Page Object Model
├── fixtures/
│   └── test-data.js          # 测试数据
├── playwright.config.js      # Playwright 配置
└── package.json
```

## 添加测试用例

1. 在 `tests/` 目录下创建新的 `.spec.js` 文件
2. 使用 `test.describe` 组织测试套件
3. 使用 `test.beforeEach` 设置测试前置条件
4. 使用 `test` 定义测试用例

示例：

```javascript
import { test, expect } from '@playwright/test';
import { SELECTORS } from '../fixtures/test-data.js';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    await expect(page.locator(SELECTORS.home.animeGrid)).toBeVisible();
  });
});
```

## Page Object Model

使用 `AppPage` 类封装页面操作：

```javascript
import { AppPage } from '../helpers/AppPage.js';

test('example', async ({ page }) => {
  const app = new AppPage(page);
  await app.gotoHome();
  await app.searchAnime('鬼灭');
  await app.clickAnimeCard(0);
});
```

## 注意事项

1. 测试使用 Chromium 浏览器
2. 测试前会自动启动 Flask 后端服务
3. 默认超时时间为 60 秒
4. 失败时会自动截图和录制视频
