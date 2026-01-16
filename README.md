# Anime1

Anime1 桌面应用 - 番剧浏览器

从 [Anime1.me](https://anime1.me) 浏览番剧的跨平台桌面应用。

## 功能特性

- 浏览 Anime1.me 番剧列表
- 分页导航
- 番剧详情查看
- **跨平台桌面应用** (Windows / macOS / Linux)

## 下载

下载对应平台的安装包：
- macOS: `Anime1.app` 或 `.dmg`
- Windows: `anime1.exe`
- Linux: `anime1`

## 使用

```bash
# 运行桌面应用
./Anime1.app/Contents/MacOS/Anime1    # macOS
./anime1                               # Linux
anime1.exe                             # Windows

# 或使用浏览器模式
python -m src.app --remote
```

## 开发

### 环境设置

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate      # Windows

# 3. 安装依赖
make install
```

### 运行应用

```bash
# 运行桌面应用
make dev

# 运行浏览器模式
make run

# 打包
make build
```

详细开发说明请查看 [DEVELOPMENT.md](DEVELOPMENT.md)

## 技术栈

- **后端**: Python + Flask
- **解析**: BeautifulSoup4
- **HTTP**: requests
- **前端**: 原生 HTML/CSS/JavaScript
- **桌面框架**: pywebview + PyInstaller

## License

MIT
