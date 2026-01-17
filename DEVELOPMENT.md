# 开发文档

## 项目结构

```
anime1-desktop/
├── frontend/          # Vue 3 前端应用
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── views/        # 页面视图
│   │   ├── router/       # 路由配置
│   │   ├── utils/        # 工具函数
│   │   └── composables/  # 组合式函数
│   └── dist/             # 构建输出
├── src/              # Python 后端
│   ├── routes/       # Flask 路由
│   ├── models/       # 数据模型
│   └── services/     # 业务逻辑
└── static/           # 静态资源(构建后)
    └── dist/         # Vue 构建产物（index.html, assets/）
```

## 开发环境设置

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

### 2. 开发模式运行

**使用 make dev（推荐）**

```bash
make dev
```

这会同时启动：
- Flask 后端: `http://localhost:5172`
- Vite 前端: `http://localhost:5173`
- 默认在 webview 窗口中打开

**环境变量选项：**

```bash
# 在浏览器中打开（推荐用于调试视频播放）
DEV_BROWSER=1 make dev

# 启用 webview 开发者工具（macOS: Option+Cmd+I）
DEV_DEBUG=1 make dev

# 跳过依赖检查和残留进程清理（加速启动）
DEV_BROWSER=1 SKIP_CHECK=1 NO_CLEANUP=1 make dev

# 组合使用
DEV_BROWSER=1 DEV_DEBUG=1 SKIP_CHECK=1 NO_CLEANUP=1 make dev
```

**直接运行脚本（备用方式）：**

```bash
# 在浏览器中打开
python scripts/dev.py --browser --skip-check --no-cleanup

# 在 webview 中打开
python scripts/dev.py --skip-check --no-cleanup

# 查看所有选项
python scripts/dev.py --help
```

**分别启动前后端（手动模式）：**

```bash
# 终端1: 启动 Flask 后端（端口 5172）
python -m src.app --debug

# 终端2: 启动 Vite 开发服务器（端口 5173）
cd frontend
npm run dev
```

访问 `http://localhost:5173`，Vite 会自动代理 `/api` 请求到 Flask。

**仅启动 Flask（使用构建后的前端）：**

```bash
# 先构建前端
cd frontend
npm run build
cd ..

# 启动 Flask
python -m src.app --debug
```

访问 `http://localhost:5172`

### 3. 构建生产版本

```bash
# 构建前端
cd frontend
npm run build
cd ..

# 构建桌面应用
python scripts/build.py
```

#### 构建脚本选项

```bash
python scripts/build.py [选项]

选项:
  --clean      清理 dist 文件夹后再构建
  --onefile    创建单文件可执行程序（默认开启）
  --debug      调试模式构建（显示更多日志）
  --remote     构建 CLI 版本（浏览器打开，无窗口）
  --installer  创建安装包（默认开启）

# 示例
python scripts/build.py                    # 默认构建（单文件 + 安装包）
python scripts/build.py --clean            # 清理后构建
python scripts/build.py --debug            # 调试模式
python scripts/build.py --remote           # CLI 版本
```

#### 构建产物

| 平台 | 输出文件 | 说明 |
|------|---------|------|
| Windows | `release/anime1-windows-x64-setup.exe` | NSIS 安装程序 |
| Windows | `release/anime1-windows-x64.zip` | 便携版（解压即用） |
| macOS | `release/anime1-macos-{version}.dmg` | DMG 磁盘映像 |
| Linux | `release/anime1-linux-x64.tar.gz` | 压缩包 |

**注意**: Windows 安装程序需要先安装 NSIS:
```bash
choco install nsis -y
```

## 技术栈

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Router** - 官方路由管理器
- **Element Plus** - Vue 3 组件库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP 客户端

### 后端
- **Flask** - Python Web 框架
- **BeautifulSoup4** - HTML 解析
- **Requests** - HTTP 库

## 主要功能

### 1. 可折叠侧边栏
- 点击底部按钮可以折叠/展开侧边栏
- 折叠后只显示图标
- 状态保存在 localStorage

### 2. 主题切换
- 支持暗黑模式、普通模式和跟随系统
- 使用 Element Plus 的暗色主题
- 主题设置保存在后端

### 3. 番剧列表
- 分页浏览
- 搜索功能
- 收藏功能
- 封面图片懒加载

### 4. 番剧详情
- 剧集列表
- 视频播放
- 收藏管理

## API 端点

所有 API 端点都在 `/api` 前缀下:

- `GET /api/anime` - 获取番剧列表
- `GET /api/anime/search` - 搜索番剧
- `GET /api/anime/:id/episodes` - 获取剧集列表
- `GET /api/favorite/list` - 获取收藏列表
- `POST /api/favorite/add` - 添加收藏
- `POST /api/favorite/remove` - 移除收藏
- `GET /api/settings/theme` - 获取主题设置
- `POST /api/settings/theme` - 保存主题设置

## 开发注意事项

1. **路由**: 所有前端路由由 Vue Router 处理,Flask 只提供 API 和 SPA 入口
2. **主题**: Element Plus 的暗色主题通过 CSS 变量实现,确保在暗色模式下正确显示
3. **构建**: 生产构建时,Vite 会将前端资源输出到 `static/dist/`,Flask 会从这个目录提供静态文件
4. **代理**: 开发模式下,Vite 会代理 `/api` 和 `/proxy` 请求到 Flask 后端

## 故障排除

### 前端无法连接后端 API
- 确保 Flask 后端正在运行在 `http://localhost:5172`
- 检查 Vite 配置中的代理设置（自动从 `FLASK_PORT` 环境变量读取）

### 端口被占用
- 运行 `make dev` 会自动检测并清理占用端口的残留进程
- 如果端口被其他应用占用，可以直接指定端口参数：`python scripts/dev.py --flask-port=5180 --vite-port=5181`

### 主题显示不正确
- 检查 `useTheme.js` 中的主题应用逻辑
- 确保 Element Plus 的暗色主题 CSS 已正确导入

### 构建失败
- 确保 Node.js 版本 >= 16
- 删除 `node_modules` 和 `package-lock.json` 后重新安装
