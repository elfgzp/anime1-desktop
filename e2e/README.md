# Anime1 Desktop E2E 测试

使用 Playwright 直接测试 Electron 应用的端到端测试套件。

## 🚀 快速开始

### 1. 检查环境

```bash
npm run test:e2e:check
```

### 2. 构建前端（必须！）

```bash
npx vite build
```

### 3. 运行测试

```bash
# 快速模式（推荐）- 59个测试
npm run test:e2e:fast

# 基本健全性测试
npm run test:e2e:sanity

# 有界面模式（可以看到 Electron 窗口）
npm run test:e2e:headed

# 查看测试报告
npm run test:e2e:report
```

## 📊 测试结果

```bash
# 快速模式
npm run test:e2e:fast
# 59 passed (约 120 秒)
```

## 📁 目录结构

```
e2e/
├── fixtures/
│   ├── index.ts           # 标准 fixtures
│   └── shared.ts          # 共享 fixtures（推荐）
├── pages/                 # Page Object 模式
│   ├── base-page.ts       # 基础页面对象
│   ├── home-page.ts       # 首页
│   ├── detail-page.ts     # 详情页
│   ├── favorites-page.ts  # 收藏页
│   ├── settings-page.ts   # 设置页
│   └── downloads-page.ts  # 下载页
├── tests/                 # 测试用例
│   ├── shared-sanity.spec.ts        # 健全性检查（8个测试）
│   ├── shared-features.spec.ts      # 功能测试（8个测试）
│   ├── shared-anime.spec.ts         # 番剧相关（5个测试）
│   ├── shared-download.spec.ts      # 下载相关（2个测试）
│   ├── shared-system.spec.ts        # 系统功能（2个测试）
│   ├── shared-performance.spec.ts   # 性能测试（3个测试）
│   ├── shared-edge-cases.spec.ts    # 边界情况（12个测试）
│   ├── shared-ui.spec.ts            # UI交互（9个测试）
│   ├── shared-data-integrity.spec.ts # 数据完整性（10个测试）
│   └── ...
├── utils/test-helpers.ts  # 测试辅助函数
├── global-setup.ts        # 全局测试前准备
├── global-teardown.ts     # 全局测试后清理
├── check-env.ts          # 环境检查脚本
└── README.md             # 本文档
```

## 📈 测试覆盖

### 1. 健全性检查 (8个测试)
- 应用启动
- 页面加载
- IPC 通信
- 基本操作

### 2. 功能测试 (8个测试)
- 页面导航
- API 功能
- 收藏操作
- 设置管理
- 窗口控制

### 3. 番剧相关 (5个测试)
- 列表获取
- 搜索功能
- 详情获取
- 剧集列表
- 缓存状态

### 4. 系统功能 (4个测试)
- 系统调用
- 更新检查
- 下载列表
- 下载历史

### 5. 性能测试 (3个测试)
- API响应时间
- 并发调用
- 页面加载

### 6. 边界情况 (12个测试)
- 空字符串搜索
- 特殊字符处理
- 不存在的数据
- 负数/超大页码
- 数据持久化
- 页面刷新
- 并发操作
- 内存管理

### 7. UI交互 (9个测试)
- 元素检查
- 键盘导航
- Tab键切换
- 滚动行为
- 窗口大小调整
- 截图测试

### 8. 数据完整性 (10个测试)
- 数据一致性
- 并发修改
- 删除隔离
- 无效参数处理
- 网络错误恢复
- 重复操作
- 状态一致性

## 🏗️ Page Object 模式

使用 Page Object 组织测试代码：

```typescript
import { test, expect } from '../fixtures/shared'
import { HomePage } from '../pages'

test('搜索功能', async ({ window, resetState }) => {
  await resetState()
  const homePage = new HomePage(window)
  
  await homePage.search('火影忍者')
  const results = await homePage.getSearchResults()
  expect(results.length).toBeGreaterThan(0)
})
```

## 🧪 测试示例

### API 测试

```typescript
test('应该能够获取番剧列表', async ({ window }) => {
  const result = await window.evaluate(async () => {
    return await window.api.anime.getList({ page: 1, pageSize: 10 })
  })
  
  expect(result).toBeDefined()
  expect(result.success).toBe(true)
})
```

### 边界情况测试

```typescript
test('搜索特殊字符应该正确处理', async ({ window }) => {
  const specialChars = ['<script>', '"test"', "'test'", '\\', '\\n']
  
  for (const char of specialChars) {
    const result = await window.evaluate(async (c) => {
      return await window.api.anime.search({ keyword: c, page: 1 })
    }, char)
    
    expect(result).toBeDefined() // 不应该崩溃
  }
})
```

### 数据持久化测试

```typescript
test('设置应该在页面刷新后保留', async ({ window, resetState }) => {
  await resetState()
  
  await window.evaluate(async () => {
    await window.api.settings.set({ key: 'test', value: 'value' })
  })
  
  await window.reload()
  
  const result = await window.evaluate(async () => {
    return await window.api.settings.get({ key: 'test' })
  })
  
  expect(result.data).toBe('value')
})
```

### UI 交互测试

```typescript
test('应该支持键盘导航', async ({ window, resetState }) => {
  await resetState()
  
  const searchInput = window.locator('input[type="text"]').first()
  await searchInput.focus()
  await searchInput.fill('火影')
  await searchInput.press('Enter')
  
  // 验证页面仍然可用
  const result = await window.evaluate(async () => {
    return await window.api.settings.getAll()
  })
  
  expect(result.success).toBe(true)
})
```

## 🔧 配置

### Playwright 配置

- **playwright.config.ts** - 标准配置
- **playwright.shared.config.ts** - 共享实例配置（推荐）

### 环境变量

- `NODE_ENV=test` - 测试模式
- `E2E_TEST=true` - E2E 测试标记
- `APP_DATA_DIR` - 测试数据目录
- `DISABLE_UPDATE_CHECK=true` - 禁用更新检查

## 🔍 调试技巧

### 1. 使用 headed 模式
```bash
npx playwright test --headed
```

### 2. 使用 debug 模式
```bash
npx playwright test --debug
```

### 3. 查看截图和视频
测试失败时会生成：
- 截图: `e2e-report/screenshots/`
- 视频: `test-results/`

### 4. 查看报告
```bash
npm run test:e2e:report
```

## 🆕 添加新测试

1. 创建测试文件: `e2e/tests/shared-my-feature.spec.ts`
2. 导入 fixture: `import { test } from '../fixtures/shared'`
3. 编写测试代码
4. 运行测试: `npx playwright test shared-my-feature.spec.ts`

## ⚠️ 注意事项

1. **必须先构建前端**: `npx vite build`
2. **IPC 修复**: Preload 脚本使用 `.cjs` 扩展名
3. **单实例锁**: 测试模式下已禁用
4. **状态重置**: 使用 `resetState()` 在测试间清理状态

## 🐛 常见问题

### ERR_FILE_NOT_FOUND
**原因**: 前端没有构建  
**解决**: `npx vite build`

### require is not defined
**原因**: Preload 脚本格式问题  
**解决**: 已修复为 `.cjs` 扩展名

### 测试超时
**原因**: Electron 启动较慢  
**解决**: 已设置 60 秒超时

## 📊 测试统计

- **测试文件**: 9个
- **测试用例**: 59个
- **代码行数**: 约 1100 行
- **运行时间**: 约 120 秒
- **通过率**: 100%
