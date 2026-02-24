# Anime1 Desktop Electron 重构技术方案

## 项目概述
将原 Python + Flask 桌面应用重构为 Electron + TypeScript 应用。

## 技术栈

### 核心架构
- **Electron Forge** - 官方推荐脚手架，提供标准化项目结构和构建流程
- **Electron 33+** - 最新稳定版本
- **Vite** - 快速构建工具（由 Electron Forge 插件提供）
- **TypeScript** - 主进程和渲染进程均使用 TypeScript

### 前端技术栈
- **Vue 3** - 前端框架（参考原项目）
- **Vue Router 4** - 路由管理
- **Pinia** - 状态管理
- **Element Plus** - UI 组件库（参考原项目）
- **Axios** - HTTP 客户端

### 主进程技术栈
- **libsql** - SQLite 数据库（Node.js 24+ 兼容）
- **Cheerio** - HTML 解析（替代 Python BeautifulSoup）
- **date-fns** - 日期处理
- **electron-log** - 日志记录
- **electron-store** - 配置存储
- **electron-updater** - 自动更新

## 项目结构

```
anime1-desktop-electron-forge/
├── forge.config.js          # Electron Forge 配置
├── vite.main.config.mjs     # 主进程 Vite 配置
├── vite.preload.config.mjs  # Preload 脚本 Vite 配置
├── vite.renderer.config.mjs # 渲染进程 Vite 配置
├── src/
│   ├── main.js              # 主进程入口
│   ├── preload.js           # Preload 脚本
│   ├── main/                # 主进程代码
│   │   ├── services/        # 业务服务
│   │   │   ├── database/    # 数据库服务
│   │   │   ├── crawler/     # 爬虫服务
│   │   │   ├── anime/       # 番剧服务
│   │   │   └── download/    # 下载服务
│   │   └── ipc/             # IPC 处理器
│   └── renderer/            # 渲染进程代码
│       ├── main.js          # 渲染进程入口
│       ├── App.vue          # 根组件
│       ├── views/           # 页面视图
│       ├── stores/          # Pinia stores
│       └── components/      # 公共组件
└── index.html               # HTML 模板
```

## 关键设计决策

### 1. 使用 Electron Forge 而非手动配置
**原因：**
- 官方维护，稳定可靠
- 自动处理主进程/渲染进程/preload 脚本的构建
- 内置打包、签名、更新机制
- 避免 vite-plugin-electron 的兼容性问题

### 2. 数据库选择 libsql 而非 better-sqlite3
**原因：**
- better-sqlite3 不支持 Node.js 24+
- libsql 是 Turso 维护的 SQLite 分支，API 兼容 better-sqlite3
- 支持 WAL 模式，性能好

### 3. 爬虫使用 Cheerio 替代 BeautifulSoup
**原因：**
- Cheerio 是 Node.js 生态中最接近 BeautifulSoup 的库
- jQuery-like API，易于使用
- 轻量，无需完整浏览器引擎

### 4. 前端保持 Vue 3 + Element Plus
**原因：**
- 与原项目技术栈一致，便于代码复用
- Element Plus 提供完善的桌面端组件
- Vue 3 Composition API 逻辑清晰

## IPC 通信设计

### Preload 脚本暴露的 API
```javascript
window.electronAPI = {
  // Anime
  getAnimeList: (params) => Promise<AnimePage>
  getAnimeDetail: (params) => Promise<Anime>
  getEpisodes: (params) => Promise<Episode[]>
  searchAnime: (params) => Promise<Anime[]>
  
  // Favorite
  getFavorites: () => Promise<Favorite[]>
  addFavorite: (params) => Promise<void>
  removeFavorite: (params) => Promise<void>
  
  // Settings
  getSettings: (key) => Promise<any>
  setSettings: (key, value) => Promise<void>
}
```

## 开发命令

```bash
# 开发模式
npm start

# 打包
npm run package

# 构建发行版
npm run make
```

## 与原项目的对应关系

| 原项目 (Python) | 新项目 (Electron) |
|----------------|------------------|
| Flask 路由 | IPC handlers |
| Jinja2 模板 | Vue 组件 |
| Peewee ORM | libsql 原生 SQL |
| BeautifulSoup | Cheerio |
| requests | axios |
| threading | Worker threads / async |
| pywebview | Electron BrowserWindow |
