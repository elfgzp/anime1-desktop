# Anime1 Desktop

Anime1.me 番剧封面浏览器 - 跨平台桌面应用版本

从 [Anime1.me](https://anime1.me) 获取番剧封面的 Web 浏览器工具。支持分页查看，自动从 Bangumi 和 AniList 获取封面。

## 功能特性

- 分页浏览 Anime1.me 番剧列表
- 自动从 Bangumi 搜索匹配番剧封面
- 自动从 AniList 作为备用搜索
- 显示番剧信息：名称、封面、集数、年份、季节、字幕组
- 支持翻页导航和页码跳转
- 简繁体中文搜索支持
- 一键获取所有封面
- **跨平台桌面应用** (Windows / macOS / Linux)

## 快速开始

### 桌面应用 (推荐)

下载对应平台的安装包：
- macOS: `.dmg` 安装包
- Windows: `.exe` 安装包
- Linux: `.AppImage` 或 `.deb`

或使用 uv 运行，无需安装依赖：

```bash
uvx anime1-desktop
```

### 常用参数

```bash
# 指定端口
uvx anime1-desktop --port 8080

# 禁用自动打开浏览器
uvx anime1-desktop --no-browser

# 开启调试模式
uvx anime1-desktop --debug
```

## 本地开发

```bash
# 克隆仓库
git clone https://github.com/elfgzp/anime1-desktop.git
cd anime1-desktop

# 使用 uv 运行 (Web 模式)
uv run python -m src.app

# 运行桌面应用
uv run python -m src.desktop
```

### 安装 uv

如果你还没有安装 uv：

```bash
# macOS
brew install uv

# 或使用 pip
pip install uv
```

## 打包发布

```bash
# macOS
./scripts/build/macos.sh

# Windows
./scripts/build/windows.sh

# Linux
./scripts/build/linux.sh
```

## 技术栈

- **后端**: Python + Flask
- **解析**: BeautifulSoup4
- **HTTP**: requests
- **前端**: 原生 HTML/CSS/JavaScript
- **桌面框架**: pywebview + PyInstaller

## License

MIT
