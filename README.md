# Anime1 Desktop

一款基于 Electron 的桌面应用，用于观看 anime1.me 的动漫内容。

## 功能特性

- 📺 **视频播放**：支持 HLS 和 MP4 流媒体播放
- 🔍 **动漫浏览**：浏览最新、热门和分类动漫
- ⭐ **收藏功能**：收藏喜爱的动漫
- 📥 **自动下载**：自动下载新剧集
- 🎨 **现代 UI**：基于 Vue 3 + Element Plus 的现代化界面
- 🔔 **自动更新**：内置自动更新功能
- ⌨️ **CLI 工具**：提供命令行工具进行快捷操作
- 📊 **性能监控**：集成 Web Vitals 性能追踪

## 技术栈

- **前端**：Vue 3, Element Plus, Pinia, Vue Router
- **后端**：Electron, better-sqlite3
- **构建**：Electron Forge, Webpack
- **测试**：Vitest (单元测试), Playwright (E2E 测试)

## 安装

### 下载预构建版本

从 [GitHub Releases](https://github.com/gzp/anime1-desktop/releases) 下载适合您平台的安装包。

### 支持的平台

- **Windows**: `.exe` 安装包 (Squirrel)
- **macOS**: `.zip` 归档 (支持 Apple Silicon 和 Intel)
- **Linux**: `.deb` (Debian/Ubuntu) 和 `.rpm` (Fedora/RHEL)

## 开发

### 环境要求

- Node.js 22+
- npm 或 yarn

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/gzp/anime1-desktop.git
cd anime1-desktop

# 安装依赖
npm install

# 启动开发模式
npm start

# 运行测试
npm test

# 构建应用
npm run make
```

## CLI 工具

应用包含一个命令行工具，可以在终端中快速操作：

```bash
# 查看应用状态
npm run cli -- status

# 查看帮助
npm run cli -- --help

# 使用 npx (如果已全局安装)
anime1 status
```

## 自动更新

应用内置自动更新功能，会在启动时检查 GitHub Releases 中的新版本。如果有可用更新，将自动下载并在下次启动时安装。

## 构建和发布

详细的构建和发布指南请查看 [BUILD.md](./BUILD.md)。

### 快速构建

```bash
# 构建所有平台
npm run make

# 构建特定平台
npm run make -- --platform=darwin
npm run make -- --platform=win32
npm run make -- --platform=linux
```

### 发布到 GitHub Releases

```bash
# 更新版本号
npm version patch  # 或 minor, major

# 推送标签 (触发 GitHub Actions 自动构建和发布)
git push origin main --tags
```

## 项目结构

```
├── src/
│   ├── main/           # Electron 主进程
│   ├── renderer/       # Vue 渲染进程
│   ├── preload/        # 预加载脚本
│   ├── services/       # 业务服务
│   ├── cli/            # 命令行工具
│   └── db/             # 数据库相关
├── assets/             # 应用资源 (图标等)
├── tests/              # 测试文件
├── .github/workflows/  # GitHub Actions CI/CD
├── forge.config.js     # Electron Forge 配置
└── package.json        # 项目配置
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License © gzp
