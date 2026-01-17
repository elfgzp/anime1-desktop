# 构建说明

## 前置要求

### Python 依赖
- Python 3.8+
- pip

### Node.js 依赖
- Node.js 16+
- npm

## 构建步骤

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -e .

# 安装前端依赖
cd frontend
npm install  # 首次安装，会生成 package-lock.json
# 或使用 npm ci 进行生产构建（更快，需要 package-lock.json）
cd ..
```

或使用 Makefile:

```bash
make install
```

**依赖管理说明**:
- `package-lock.json` 已提交到 Git，确保依赖版本一致性
- 开发时使用 `npm install`，构建时使用 `npm ci`
- 前端依赖安装在 `frontend/node_modules/` 目录下

### 2. 构建前端

```bash
cd frontend
npm run build
cd ..
```

构建产物会输出到 `static/dist/` 目录。

### 3. 构建桌面应用

```bash
# 使用 build.py
python build.py --clean

# 或使用 Makefile
make build
```

## 构建流程说明

### 完整构建流程

1. **前端构建** (`frontend/`)
   - 运行 `npm ci` 安装依赖
   - 运行 `npm run build` 构建 Vue 应用
   - 输出到 `static/dist/`

2. **Python 应用构建** (`build.py`)
   - 使用 PyInstaller 打包 Python 应用
   - 包含前端构建产物 (`static/dist/`)
   - 包含模板文件 (`templates/`)
   - 包含静态资源 (`static/`)

### 构建产物

- **Windows**: `dist/Anime1.exe` (onefile) 或 `dist/Anime1/` (onedir)
- **macOS**: `dist/Anime1.app/`
- **Linux**: `dist/Anime1` (onefile) 或 `dist/Anime1/` (onedir)

## GitHub Actions 构建

GitHub Actions 会自动执行以下步骤:

1. 设置 Node.js 环境
2. 安装前端依赖 (`npm ci`)
3. 构建前端 (`npm run build`)
4. 设置 Python 环境
5. 安装 Python 依赖
6. 构建桌面应用
7. 打包发布产物

## 本地开发

### 开发模式（前后端分离）

```bash
# 终端1: 启动 Flask 后端
python -m src.app --debug

# 终端2: 启动 Vite 开发服务器
cd frontend
npm run dev
```

访问 `http://localhost:5173` (Vite 会自动代理 API 请求)

### 开发模式（使用构建后的前端）

```bash
# 构建前端
cd frontend
npm run build
cd ..

# 启动 Flask
python -m src.app --debug
```

访问 `http://localhost:5172`

## 故障排除

### 前端构建失败

- 确保 Node.js 版本 >= 16
- 删除 `node_modules` 和 `package-lock.json` 后重新安装
- 检查 `frontend/package.json` 中的依赖版本

### 构建产物缺少前端资源

- 确保先运行 `npm run build` 构建前端
- 检查 `static/dist/` 目录是否存在
- 查看 `build.py` 的日志，确认前端构建产物被包含

### PyInstaller 构建失败

- 确保所有 Python 依赖已安装
- 检查 `build.py` 中的 hidden imports 是否完整
- 查看构建日志中的错误信息

## 验证构建

```bash
# 验证前端构建
bash scripts/verify-frontend.sh

# 验证所有脚本
bash scripts/verify-scripts.sh
```
