# 更新日志

## 2025-02-26

### 修复

#### 1. 暗黑模式状态保存
- **问题**: 主题设置在重启后丢失
- **解决**: 使用 JSON.stringify/JSON.parse 正确序列化和反序列化设置值
- **文件**: 
  - `src/renderer/views/Settings.vue` - 加载时解析 JSON
  - `src/renderer/stores/settings.ts` - 保存时序列化

## [2.0.0] - 2026-02-26

### Added
- Electron + Vue 3 + TypeScript 重构
- 自动下载服务（配置、筛选规则、定时调度）
- 更新服务（electron-updater + GitHub Releases）
- 9个 E2E 测试
- 功能对比文档

### Changed
- 重写 GitHub Actions 为 Electron 模式
- 升级构建系统为 electron-builder

### Fixed
- 图标和应用名称显示问题
- Dock 栏图标显示

#### 2. 收藏功能增强
- **问题**: 收藏列表缺少播放进度和更新标记
- **解决**: 
  - 增强 `favorite:list` IPC 接口，返回播放进度和更新状态
  - 添加 `getLatestPlaybackForAnime` 数据库方法
  - 实现正确的排序逻辑
- **文件**:
  - `src/main/ipc/index.ts` - 增强收藏列表数据
  - `src/main/services/database/index.ts` - 添加播放历史查询
  - `src/renderer/views/Favorites.vue` - 显示进度条和更新标记
  - `src/renderer/stores/favorite.ts` - 添加批量检查状态方法

#### 3. macOS 原生全屏
- **问题**: 最大化使用 setBounds() 而非原生全屏
- **解决**: macOS 使用 setFullScreen() 进入独立 Space
- **文件**: `src/main/window.ts`

#### 4. 收藏日期显示
- **问题**: 使用了错误的字段名 createdAt
- **解决**: 统一使用 addedAt 字段
- **文件**: `src/renderer/views/Favorites.vue`

#### 5. 应用图标
- **问题**: resources 目录缺少图标文件
- **解决**: 添加 icon.icns 和 icon.ico
- **文件**: `resources/`

### 新增

- 开发工具脚本 (`scripts/`)
  - `quick-fix.sh` - 快速修复常见问题
  - `debug-template.js` - 调试脚本模板
- 开发文档 (`DEVELOPMENT.md`)

## 项目初始化

- Electron + Vue 3 + TypeScript + Vite 基础架构
- 番剧列表、详情、播放功能
- 收藏、播放历史、下载管理
- 暗黑模式支持
