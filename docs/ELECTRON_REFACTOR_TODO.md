# Electron 重构任务清单

## 第一阶段：项目初始化 (Week 1)

### 1.1 环境准备
- [ ] 安装 Node.js 20+ 
- [ ] 安装 pnpm / yarn / npm
- [ ] 配置 TypeScript 开发环境
- [ ] 配置 ESLint + Prettier

### 1.2 项目结构搭建
```
mkdir -p src/{main/{ipc,services/{anime,crawler,database,download,update},utils},preload,renderer/{components,views,composables,stores,router,utils,types},shared/{constants,types,utils}}
mkdir -p resources build tests/{main,renderer,e2e}
```

### 1.3 配置文件
- [ ] `package.json` - 依赖和脚本
- [ ] `tsconfig.json` - TypeScript 配置
- [ ] `vite.config.ts` - Vite + Electron 配置
- [ ] `electron-builder.yml` - 打包配置
- [ ] `.eslintrc.cjs` - ESLint 配置
- [ ] `.prettierrc` - Prettier 配置

### 1.4 核心依赖安装
```bash
# Electron 核心
electron electron-builder vite-plugin-electron

# TypeScript
typescript vue-tsc @types/node

# Vue 3 生态
vue vue-router pinia @vitejs/plugin-vue

# UI 组件
element-plus @element-plus/icons-vue

# 数据库
better-sqlite3 @types/better-sqlite3

# 爬虫/HTTP
axios cheerio

# 工具库
lodash-es date-fns
```

---

## 第二阶段：主进程开发 (Week 2-3)

### 2.1 入口文件
- [ ] `src/main/index.ts` - 主进程入口
- [ ] `src/main/window.ts` - 窗口管理
- [ ] 单实例锁实现
- [ ] 系统托盘集成

### 2.2 IPC 层
- [ ] `src/main/ipc/index.ts` - IPC 注册中心
- [ ] `src/main/ipc/anime.ts` - 番剧相关 IPC
- [ ] `src/main/ipc/favorite.ts` - 收藏相关 IPC
- [ ] `src/main/ipc/settings.ts` - 设置相关 IPC
- [ ] `src/main/ipc/download.ts` - 下载相关 IPC
- [ ] `src/main/ipc/system.ts` - 系统相关 IPC

### 2.3 爬虫服务
- [ ] `src/main/services/crawler/index.ts` - 爬虫服务入口
- [ ] HTTP 客户端封装 (axios)
- [ ] Anime1 列表解析
- [ ] Anime1 详情解析
- [ ] 剧集列表解析
- [ ] Bangumi API 集成
- [ ] 视频 URL 提取

### 2.4 数据库服务
- [ ] `src/main/services/database/index.ts` - 数据库连接
- [ ] `src/main/services/database/migration.ts` - 迁移脚本
- [ ] 收藏表操作
- [ ] 封面缓存表操作
- [ ] 播放历史表操作
- [ ] 设置表操作

### 2.5 番剧服务
- [ ] `src/main/services/anime/index.ts` - 番剧服务
- [ ] 番剧列表管理
- [ ] 番剧详情获取
- [ ] 剧集列表获取
- [ ] 搜索功能
- [ ] 缓存管理

### 2.6 下载服务
- [ ] `src/main/services/download/index.ts` - 下载服务
- [ ] 下载任务管理
- [ ] 断点续传
- [ ] 进度跟踪
- [ ] 队列管理

### 2.7 更新服务
- [ ] `src/main/services/update/index.ts` - 更新服务
- [ ] 更新检查
- [ ] 自动下载
- [ ] 自动安装

---

## 第三阶段：渲染进程开发 (Week 4-5)

### 3.1 基础配置
- [ ] `src/renderer/main.ts` - Vue 入口
- [ ] `src/renderer/App.vue` - 根组件
- [ ] Element Plus 配置
- [ ] 路由配置
- [ ] Pinia Store 配置

### 3.2 类型定义
- [ ] `src/renderer/types/anime.ts` - 番剧类型
- [ ] `src/renderer/types/api.ts` - API 类型
- [ ] `src/shared/types/index.ts` - 共享类型

### 3.3 Store 实现
- [ ] `src/renderer/stores/anime.ts` - 番剧 Store
- [ ] `src/renderer/stores/favorite.ts` - 收藏 Store
- [ ] `src/renderer/stores/settings.ts` - 设置 Store
- [ ] `src/renderer/stores/download.ts` - 下载 Store
- [ ] `src/renderer/stores/history.ts` - 历史 Store

### 3.4 Composables
- [ ] `src/renderer/composables/useTheme.ts` - 主题
- [ ] `src/renderer/composables/usePlayer.ts` - 播放器
- [ ] `src/renderer/composables/useScrollRestore.ts` - 滚动恢复
- [ ] `src/renderer/composables/useShortcut.ts` - 快捷键
- [ ] `src/renderer/composables/useDownload.ts` - 下载

### 3.5 页面视图
- [ ] `src/renderer/views/Home.vue` - 首页/番剧列表
- [ ] `src/renderer/views/Detail.vue` - 番剧详情
- [ ] `src/renderer/views/Favorites.vue` - 收藏页面
- [ ] `src/renderer/views/History.vue` - 播放历史
- [ ] `src/renderer/views/Downloads.vue` - 下载管理
- [ ] `src/renderer/views/Settings.vue` - 设置页面

### 3.6 组件
- [ ] `src/renderer/components/Layout.vue` - 布局组件
- [ ] `src/renderer/components/Sidebar.vue` - 侧边栏
- [ ] `src/renderer/components/AnimeCard.vue` - 番剧卡片
- [ ] `src/renderer/components/AnimeGrid.vue` - 番剧网格
- [ ] `src/renderer/components/VideoPlayer.vue` - 视频播放器
- [ ] `src/renderer/components/SearchBar.vue` - 搜索栏
- [ ] `src/renderer/components/Pagination.vue` - 分页器
- [ ] `src/renderer/components/EmptyState.vue` - 空状态
- [ ] `src/renderer/components/LoadingState.vue` - 加载状态

---

## 第四阶段：数据迁移 (Week 5)

### 4.1 数据库迁移
- [ ] 分析原数据库结构
- [ ] 编写迁移脚本
- [ ] 数据兼容性测试
- [ ] 回滚方案准备

### 4.2 配置迁移
- [ ] 原配置读取
- [ ] 新配置格式转换
- [ ] 配置导入导出

---

## 第五阶段：功能完善 (Week 6)

### 5.1 系统集成
- [ ] 系统托盘菜单
- [ ] 全局快捷键
- [ ] 窗口状态记忆
- [ ] 开机启动选项

### 5.2 高级功能
- [ ] 自动下载调度器
- [ ] 播放进度同步
- [ ] 多语言支持准备
- [ ] 崩溃报告

### 5.3 性能优化
- [ ] 虚拟滚动
- [ ] 图片懒加载
- [ ] 代码分割
- [ ] 启动优化

---

## 第六阶段：测试 (Week 7)

### 6.1 单元测试
- [ ] 主进程服务测试
- [ ] Store 测试
- [ ] Composables 测试
- [ ] 工具函数测试

### 6.2 E2E 测试
- [ ] 基础流程测试
- [ ] 播放流程测试
- [ ] 下载流程测试
- [ ] 设置流程测试

### 6.3 兼容性测试
- [ ] macOS Intel 测试
- [ ] macOS Apple Silicon 测试
- [ ] Windows 10/11 测试
- [ ] Linux 测试

---

## 第七阶段：发布准备 (Week 8)

### 7.1 打包配置
- [ ] macOS 签名配置
- [ ] Windows 签名配置
- [ ] 图标资源准备
- [ ] 安装程序配置

### 7.2 CI/CD
- [ ] GitHub Actions 配置
- [ ] 自动化测试
- [ ] 自动化打包
- [ ] 自动发布

### 7.3 文档
- [ ] README 更新
- [ ] 开发文档
- [ ] 用户手册
- [ ] 更新日志

---

## 关键检查点

### Checkpoint 1: 基础架构完成
- [ ] 项目可以正常启动
- [ ] 窗口可以正常显示
- [ ] IPC 通信正常

### Checkpoint 2: 数据层完成
- [ ] 数据库可以正常读写
- [ ] 数据迁移脚本可用
- [ ] 爬虫可以获取数据

### Checkpoint 3: 核心功能完成
- [ ] 番剧列表显示正常
- [ ] 详情页面正常
- [ ] 搜索功能正常
- [ ] 收藏功能正常

### Checkpoint 4: 发布准备完成
- [ ] 所有测试通过
- [ ] 打包成功
- [ ] 签名配置完成

---

## 备注

### Python → TypeScript 映射速查

| Python (Flask) | TypeScript (Electron) |
|---------------|----------------------|
| Flask Blueprint | IPC Handler |
| Peewee Model | Interface + SQL |
| requests | axios |
| BeautifulSoup | cheerio |
| ThreadPoolExecutor | worker_threads |
| SQLite | better-sqlite3 |
| logging | electron-log |
| argparse | electron-store |

### 文件迁移对应表

| 原文件 | 新文件 |
|-------|-------|
| `src/app.py` | `src/main/index.ts` |
| `src/desktop.py` | `src/main/window.ts` |
| `src/routes/anime.py` | `src/main/ipc/anime.ts` |
| `src/models/anime.py` | `src/shared/types/anime.ts` |
| `src/models/database.py` | `src/main/services/database/index.ts` |
| `src/parser/anime1_parser.py` | `src/main/services/crawler/anime1.ts` |
| `src/services/anime_cache_service.py` | `src/main/services/anime/cache.ts` |
| `frontend/src/App.vue` | `src/renderer/App.vue` |
