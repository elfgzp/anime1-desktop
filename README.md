# Anime1 Desktop

从 [Anime1.me](https://anime1.me) 浏览和观看番剧的桌面客户端，支持 Windows、macOS 和 Linux。

## 功能特性

- 🎬 浏览 Anime1.me 上的所有番剧
- 📺 在线观看高清视频
- 🔍 快速搜索番剧
- 💾 收藏喜欢的番剧
- ⬇️ 自动下载番剧（支持按年份、季节过滤）
- 🖥️ 原生桌面应用体验
- 🐳 支持 Docker/NAS 部署（群晖、威联通等）
- 🎨 现代化 Vue 3 前端界面
- 🌙 支持暗黑模式

## 预览

![Anime1 Desktop](screenshots/home-page.png)

查看 [产品功能介绍](docs/FEATURES.md) 了解更多功能。

## 下载安装

### Windows

1. 从 [GitHub Releases](https://github.com/elfgzp/anime1-desktop/releases) 下载 `anime1-windows-x64.zip`
2. 解压 zip 文件
3. 双击运行 `Anime1.exe`

### macOS

#### Homebrew 安装（推荐）

```bash
# 添加 tap
brew tap elfgzp/homebrew-tap

# 安装 anime1
brew install --cask anime1
```

#### 手动安装

1. 从 [GitHub Releases](https://github.com/elfgzp/anime1-desktop/releases) 下载 `anime1-macos-{version}.dmg`
2. 双击 DMG 文件挂载
3. 将 `Anime1.app` 拖拽到应用程序文件夹
4. 在启动台或应用程序文件夹中打开应用

> 💡 **提示**：首次打开时如果遇到安全提示，请右键点击应用选择"打开"，或在"系统设置 → 隐私与安全性"中允许运行。

### Linux

1. 从 [GitHub Releases](https://github.com/elfgzp/anime1-desktop/releases) 下载对应版本：
   - **x64**: `anime1-linux-x64.tar.gz`
   - **ARM64**: `anime1-linux-arm64.tar.gz`
2. 解压并运行：
   ```bash
   tar -xzf anime1-linux-*.tar.gz
   chmod +x Anime1
   ./Anime1
   ```

### Docker / NAS 部署

支持在群晖、威联通等 NAS 或 Linux 服务器上通过 Docker 部署：

```bash
# 快速开始
docker run -d \
  --name anime1 \
  -p 5172:5172 \
  -v anime1_data:/app/data \
  ghcr.io/elfgzp/anime1-desktop:latest
```

详细配置（数据持久化、自动下载、更新策略等）请参考 [Docker 部署指南](docs/DOCKER.md)。

## 使用说明

1. 启动应用后，浏览番剧列表
2. 点击番剧查看详情和集数
3. 选择集数开始观看
4. 使用收藏功能保存喜欢的番剧

## 开发

### 快速开始

```bash
# 安装依赖
make install

# 启动开发服务器（同时启动 Flask + Vite）
make dev-server

# 访问 http://localhost:5173
```

更多开发信息请查看 [DEVELOPMENT.md](DEVELOPMENT.md)

## 反馈与支持

如有问题或建议，欢迎在 [GitHub Issues](https://github.com/elfgzp/anime1-desktop/issues) 中反馈。

---

**开发者文档**：查看 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发、构建和部署相关信息。
