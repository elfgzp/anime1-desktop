# Development Guide

## 环境要求

- Python 3.8+
- pip
- 虚拟环境支持（venv）

## Quick Start

### 1. 创建虚拟环境

```bash
# 创建 venv 虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```

### 2. 安装依赖

```bash
# 方式一：使用 Makefile（推荐，会自动创建 venv）
make install

# 方式二：手动安装
pip install --upgrade pip
pip install -e .
```

### 3. 运行应用

```bash
# 运行桌面应用
make dev

# 或运行在浏览器中
make run
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make dev` | Run desktop app in development mode |
| `make run` | Run in browser (CLI mode) |
| `make verify-deps` | Verify required packages |
| `make build` | Build desktop application |
| `make build-onefile` | Build as single executable |
| `make install-dmg` | Install create-dmg (macOS) |
| `make dmg` | Create DMG for macOS |
| `make clean` | Clean build artifacts |
| `make clean-all` | Clean everything |
| `make test` | Run tests |

## Project Structure

```
anime1-desktop/
├── src/              # Python source code
│   ├── app.py        # Flask application
│   ├── desktop.py    # Desktop app entry (pywebview)
│   ├── config.py     # Configuration
│   ├── routes/       # Flask routes
│   ├── parser/       # Anime1.me parsers
│   ├── models/       # Data models
│   └── utils/        # Utility functions
├── templates/        # HTML templates
├── static/           # CSS, JS, assets
├── build.py          # PyInstaller build script
└── Makefile          # Build automation
```

## Building for Distribution

### Standard Build (Directory)

```bash
make build
```

Output: `dist/Anime1.app` (macOS) or `dist/anime1/` (Linux)

### Single File Build

```bash
make build-onefile
```

Output: `dist/anime1` (Linux/macOS) or `dist/anime1.exe` (Windows)

### macOS DMG

```bash
make install-dmg  # Install create-dmg tool first
make dmg          # Create DMG
```

Output: `dist/Anime1.dmg`

## 开发环境设置

### 使用 venv 虚拟环境（推荐）

项目使用 Python 标准库的 `venv` 模块来管理虚拟环境。

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate      # Windows

# 3. 安装依赖
pip install --upgrade pip
pip install -e .

# 4. 验证安装
python -c "import PyInstaller; import webview; print('OK')"
```

### 依赖说明

主要依赖包（在 `pyproject.toml` 中定义）：
- **flask** >= 2.3.0 - Web 框架
- **beautifulsoup4** >= 4.12.0 - HTML 解析
- **requests** >= 2.31.0 - HTTP 请求
- **pywebview** >= 4.0.0 - 桌面 GUI 框架
- **pyinstaller** >= 6.0.0 - 应用打包工具
- **pillow** >= 10.0.0 - 图像处理
- **hanziconv** >= 0.3.2 - 简繁转换

### 开发依赖

```bash
pip install -e ".[dev]"
```

包含：
- **pytest** >= 7.0.0 - 测试框架

## 故障排查

### macOS 应用无法启动

如果编译后的 macOS 应用（`Anime1.app`）无法启动，可以按以下步骤排查：

#### 1. 检查应用签名和权限

```bash
# 检查签名状态
codesign -dv --verbose=4 dist/Anime1.app

# 验证签名
codesign --verify --verbose dist/Anime1.app

# 检查架构（确保是 arm64 或与你的 Mac 匹配）
file dist/Anime1.app/Contents/MacOS/Anime1

# 检查执行权限
ls -la dist/Anime1.app/Contents/MacOS/Anime1
```

#### 2. 检查 Quarantine 属性

```bash
# 查看 quarantine 属性
xattr -l dist/Anime1.app

# 如果存在 quarantine 属性，清除它
sudo xattr -r -d com.apple.quarantine dist/Anime1.app
```

#### 3. 检查 Gatekeeper 状态

```bash
# 查看 Gatekeeper 状态
spctl --status
```

如果应用被 Gatekeeper 拦截：
- **方法一**：右键点击应用 → "打开"，会触发一次性确认对话框
- **方法二**：在"系统设置 → 隐私与安全"中，找到被阻止的应用，点击"仍要打开"

#### 4. 直接运行查看错误信息

```bash
# 直接运行可执行文件查看错误
dist/Anime1.app/Contents/MacOS/Anime1
```

常见错误：
- **缺少依赖模块**：检查 `pyproject.toml` 中是否包含所有依赖，并在 `build.py` 的 `hidden_imports` 中添加
- **模块导入错误**：确保所有 Python 依赖都已正确打包

#### 5. 检查系统日志

```bash
# 查看系统日志中的应用启动信息
log show --predicate 'process == "Anime1"' --last 5m --style compact
```

#### 6. 重新编译

如果以上步骤都无法解决问题，尝试清理后重新编译：

```bash
make clean
make build
```

### 常见问题

**Q: 应用启动后立即退出，没有错误提示？**

A: 这通常是因为缺少 Python 依赖模块。检查：
1. 所有依赖是否在 `pyproject.toml` 中声明
2. 所有动态导入的模块是否在 `build.py` 的 `hidden_imports` 中

**Q: macOS 提示"无法打开，因为来自身份不明的开发者"？**

A: 这是正常的，因为应用使用了 adhoc 签名（开发签名）。解决方法：
1. 右键点击应用 → "打开"
2. 或在"系统设置 → 隐私与安全"中允许

**Q: 应用签名显示 "adhoc" 是否正常？**

A: 是的，对于开发和测试用途，adhoc 签名是正常的。如果要发布到 App Store 或让用户更容易信任，需要使用 Developer ID 签名和 Apple 公证。
