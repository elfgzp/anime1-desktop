# Anime1 Desktop Electron 开发指南

## 项目概述

- **技术栈**: Electron 40.4.0 + Vue 3.5.28 + TypeScript 5.9.3 + Vite 5.4.21
- **状态管理**: Pinia
- **UI 框架**: Element Plus
- **数据库**: better-sqlite3

## 快速启动

```bash
# 安装依赖
npm install

# 开发模式（热重载）
npm run dev

# 构建
npm run build

# 仅构建前端
npm run build:fast
```

## 项目结构

```
/Users/gzp/Github/anime1-desktop-electron/
├── src/
│   ├── main/              # Electron 主进程
│   │   ├── index.ts       # 主入口
│   │   ├── window.ts      # 窗口管理
│   │   ├── ipc/           # IPC 通信
│   │   └── services/      # 业务服务
│   │       ├── database/  # 数据库操作
│   │       ├── anime/     # 番剧服务
│   │       └── ...
│   ├── renderer/          # 渲染进程 (Vue)
│   │   ├── main.ts        # 渲染进程入口
│   │   ├── App.vue        # 根组件
│   │   ├── views/         # 页面
│   │   ├── stores/        # Pinia Store
│   │   └── components/    # 组件
│   ├── preload/           # 预加载脚本
│   └── shared/            # 共享类型和常量
├── resources/             # 应用资源（图标等）
├── e2e/                   # Playwright 测试
└── screenshots/           # 调试截图输出
```

## 快速开始（推荐）

```bash
# 1. 启动应用
npm run dev

# 2. 运行系统检查（另一个终端）
./scripts/quick-fix.sh check

# 3. 截图验证
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/" screenshots/test.png
```

## 调试方法

### 快速修复脚本

```bash
# 系统检查（推荐每次启动后运行）
./scripts/quick-fix.sh check

# 重置数据库（解决数据问题）
./scripts/quick-fix.sh db

# 设置暗黑模式
./scripts/quick-fix.sh theme

# 清理缓存并重启
./scripts/quick-fix.sh cache

# 一键修复所有问题
./scripts/quick-fix.sh all
```

### 1. 查看 Electron 日志

日志文件位置:
- macOS: `~/Library/Application Support/anime1-desktop-electron/logs/main.log`

```bash
# 实时查看日志
tail -f ~/Library/Application\ Support/anime1-desktop-electron/logs/main.log
```

### 2. 打开 DevTools

- 快捷键: `Cmd/Ctrl + Shift + D`
- 或通过代码: `mainWindow.webContents.openDevTools()`

### 3. 使用 Playwright 连接调试

```bash
# 1. 先启动应用
npm run dev

# 2. 获取 CDP 连接地址
curl -s http://localhost:9222/json/list

# 3. 使用 Playwright 截图验证
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/" screenshots/test.png
```

### 4. JavaScript 调试脚本

创建 `debug.js`:
```javascript
const { chromium } = require('playwright-core');

(async () => {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const context = browser.contexts()[0];
    const page = context.pages()[0];
    
    // 截图
    await page.screenshot({ path: 'screenshots/debug.png', fullPage: true });
    
    // 获取页面文本
    const text = await page.evaluate(() => document.body.innerText);
    console.log(text.substring(0, 500));
    
    // 检查 HTML class
    const htmlClass = await page.evaluate(() => document.documentElement.className);
    console.log('HTML class:', htmlClass);
    
    await browser.close();
})();
```

运行: `node debug.js`

## 常见问题及解决方案

### 1. 暗黑模式不生效或重启后丢失

**原因**: 设置存储格式不一致

**解决**:
```typescript
// settings.ts - 保存时使用 JSON.stringify
async function setTheme(value: ThemeMode) {
  await window.api.settings.set({
    key: 'theme',
    value: JSON.stringify(value)  // 必须序列化
  })
  applyTheme(value)
}

// 加载时解析
async function loadSettings() {
  const result = await window.api.settings.getAll()
  if (result.success && result.data) {
    // 尝试解析 JSON
    let theme = result.data.theme
    try {
      theme = JSON.parse(theme)
    } catch {
      // 已经是字符串，直接使用
    }
    applyTheme(theme)
  }
}
```

### 2. 收藏按钮显示异常 / isFavorite 报错

**原因**: Pinia store 的 computed getter 在组件渲染时可能未初始化

**解决**:
```vue
<!-- Home.vue -->
<template>
  <!-- 使用可选链或函数包装 -->
  <el-button
    :icon="isAnimeFavorite(anime.id) ? StarFilled : Star"
    :class="{ active: isAnimeFavorite(anime.id) }"
  />
</template>

<script>
function isAnimeFavorite(animeId: string): boolean {
  try {
    return favoritesStore.isFavorite(animeId)
  } catch {
    return false
  }
}
</script>
```

### 3. macOS 全屏不进入原生全屏

**原因**: 使用了 `setBounds()` 而不是 `setFullScreen()`

**解决**:
```typescript
// window.ts
ipcMain.handle('window:maximize', () => {
  const win = this.mainWindow
  if (!win) return { success: false, maximized: false }
  
  if (process.platform === 'darwin') {
    // macOS: 使用原生全屏
    const isFullScreen = win.isFullScreen()
    win.setFullScreen(!isFullScreen)
    return { success: true, maximized: !isFullScreen }
  } else {
    // Windows/Linux: 使用普通最大化
    if (win.isMaximized()) {
      win.unmaximize()
      return { success: true, maximized: false }
    } else {
      win.maximize()
      return { success: true, maximized: true }
    }
  }
})
```

### 4. 收藏日期显示不正确

**原因**: 数据库字段是 `addedAt`，但前端使用了 `createdAt`

**解决**:
```typescript
// 统一使用 addedAt
interface FavoriteAnime {
  animeId: string
  title: string
  addedAt: number      // 不是 createdAt
  updatedAt: number
  // ...
}
```

### 5. 收藏列表缺少播放进度/更新标记

**原因**: IPC 层没有返回增强数据

**解决**:
```typescript
// ipc/index.ts - favorite:list
ipcMain.handle('favorite:list', async () => {
  const favorites = await databaseService.getFavorites()
  const animeMap = animeService.getAnimeMap()  // 需要实现此方法
  
  const enhancedFavorites = favorites.map(fav => {
    // 获取播放进度
    const playback = databaseService.getLatestPlaybackForAnime(fav.animeId)
    
    // 检查更新
    const currentAnime = animeMap.get(fav.animeId)
    const currentEpisode = currentAnime?.episode ?? fav.episode ?? 0
    const hasUpdate = currentEpisode > (fav.lastEpisode ?? 0)
    
    return {
      ...fav,
      playbackProgress: playback ? {
        episodeNum: playback.episodeNum,
        positionFormatted: formatDuration(playback.positionSeconds),
        progressPercent: calculateProgress(playback)
      } : null,
      hasUpdate,
      newEpisodeCount: hasUpdate ? currentEpisode - fav.lastEpisode : 0
    }
  })
  
  // 排序: 有更新优先
  enhancedFavorites.sort((a, b) => {
    if (a.hasUpdate !== b.hasUpdate) return a.hasUpdate ? -1 : 1
    return b.newEpisodeCount - a.newEpisodeCount
  })
  
  return { success: true, data: enhancedFavorites }
})
```

### 6. 应用图标不显示

**解决**:
```bash
# 确保 resources 目录有图标
resources/
├── icon.icns    # macOS
├── icon.ico     # Windows
└── icon.png     # Linux
```

参考 `electron-builder.yml` 配置。

## 开发工作流

### 添加新功能的标准流程

1. **定义类型** (`src/shared/types/`)
```typescript
// anime.ts
export interface NewFeature {
  id: string
  name: string
}
```

2. **实现 IPC** (`src/main/ipc/index.ts`)
```typescript
ipcMain.handle('feature:action', async (_, params) => {
  try {
    const result = await service.doSomething(params)
    return { success: true, data: result }
  } catch (error) {
    return { success: false, error: { message: String(error) } }
  }
})
```

3. **更新 Preload** (`src/preload/index.ts`)
```typescript
export interface ElectronAPI {
  feature: {
    action: (params: any) => Promise<any>
  }
}
```

4. **创建 Store** (`src/renderer/stores/`)
```typescript
export const useFeatureStore = defineStore('feature', () => {
  const items = ref<NewFeature[]>([])
  
  async function loadItems() {
    const result = await window.api.feature.action({})
    if (result.success) {
      items.value = result.data
    }
  }
  
  return { items, loadItems }
})
```

5. **创建组件** (`src/renderer/views/`)
```vue
<template>
  <div>
    <div v-for="item in store.items" :key="item.id">
      {{ item.name }}
    </div>
  </div>
</template>

<script setup>
import { useFeatureStore } from '../stores'
const store = useFeatureStore()
</script>
```

### 调试检查清单

- [ ] 主进程日志是否正常输出
- [ ] IPC 调用是否成功返回
- [ ] Store 状态是否正确更新
- [ ] 组件是否正确响应状态变化
- [ ] 截图验证 UI 显示是否正确

### 截图验证命令

```bash
# 首页
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/" screenshots/home.png

# 收藏页
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/#/favorites" screenshots/favorites.png

# 设置页
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/#/settings" screenshots/settings.png
```

## 数据库操作

```bash
# 查看收藏
sqlite3 ~/Library/Application\ Support/anime1-desktop-electron/anime1.db \
  "SELECT * FROM favorite_anime;"

# 查看设置
sqlite3 ~/Library/Application\ Support/anime1-desktop-electron/anime1.db \
  "SELECT * FROM settings;"

# 插入测试数据
sqlite3 ~/Library/Application\ Support/anime1-desktop-electron/anime1.db \
  "INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', '\"dark\"');"
```

## 测试

```bash
# 运行 E2E 测试
npm run test:e2e

# 调试模式
npm run test:e2e:debug
```

## 性能优化

1. **数据库查询**: 使用索引，避免全表扫描
2. **图片加载**: 使用懒加载，骨架屏占位
3. **IPC 通信**: 批量请求，减少往返次数
4. **Store 状态**: 使用 computed 缓存计算结果

## 开发工具

### 快速修复脚本 (`scripts/quick-fix.sh`)

一键解决常见问题：

```bash
# 系统检查
./scripts/quick-fix.sh check

# 重置数据库
./scripts/quick-fix.sh db

# 设置暗黑模式
./scripts/quick-fix.sh theme

# 清理缓存并重启
./scripts/quick-fix.sh cache

# 一键修复所有
./scripts/quick-fix.sh all
```

### 调试模板 (`scripts/debug-template.js`)

复制并修改此模板来调试：

```bash
cp scripts/debug-template.js my-debug.js
# 编辑 my-debug.js 添加调试逻辑
node my-debug.js
```

### 常用调试代码片段

```javascript
// 检查 Pinia Store
const storeInfo = await page.evaluate(() => {
    const pinia = window.__pinia;
    return {
        stores: Object.keys(pinia.state.value),
        animeCount: pinia.state.value.anime?.animeList?.length
    };
});

// 调用 API
const result = await page.evaluate(async () => {
    return await window.api.anime.getList({ page: 1 });
});

// 截图对比
await page.screenshot({ path: `screenshots/${Date.now()}.png` });
```

## 安全注意事项

1. **XSS 防护**: 使用 DOMPurify 净化用户输入
2. **IPC 安全**: 验证所有 IPC 参数
3. **CORS**: 视频代理服务处理跨域

## 参考资料

- [Electron 文档](https://www.electronjs.org/docs)
- [Vue 3 文档](https://vuejs.org/guide/)
- [Element Plus 文档](https://element-plus.org/)
- [better-sqlite3 文档](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md)
