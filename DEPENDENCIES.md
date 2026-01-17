# 依赖管理说明

## 前端依赖 (npm)

### 文件位置

- `frontend/package.json` - 依赖声明（已提交到 Git）
- `frontend/package-lock.json` - 锁定依赖版本（**必须提交到 Git**）
- `frontend/node_modules/` - 依赖安装目录（已添加到 .gitignore）

### 安装依赖

```bash
# 开发环境（首次安装）
cd frontend
npm install
cd ..

# 生产构建（CI/CD，更快且更可靠）
cd frontend
npm ci  # 需要 package-lock.json
cd ..
```

### 为什么需要 package-lock.json？

1. **版本一致性**: 确保所有环境（开发、CI/CD、生产）使用相同的依赖版本
2. **构建可重现**: 避免因依赖版本差异导致的构建问题
3. **安全性**: 锁定已知安全的依赖版本，避免自动更新引入漏洞

### 更新依赖

```bash
cd frontend

# 更新单个包
npm update <package-name>

# 更新所有包到最新版本（会更新 package-lock.json）
npm update

# 添加新依赖
npm install <package-name>

# 添加开发依赖
npm install --save-dev <package-name>
```

**重要**: 更新依赖后，必须提交 `package-lock.json` 到 Git。

## 后端依赖 (Python)

### 文件位置

- `pyproject.toml` - 依赖声明（已提交到 Git）
- `uv.lock` - 锁定依赖版本（如果使用 uv，已提交到 Git）
- `*.egg-info/` - Python 包信息（已添加到 .gitignore）

### 安装依赖

```bash
# 开发环境
pip install -e .

# 生产环境
pip install -e .
```

## Git 忽略规则

### 前端相关（已添加到 .gitignore）

```
node_modules/          # npm 依赖目录
frontend/dist/         # 前端构建输出
frontend/.vite/        # Vite 缓存
static/dist/           # 构建后的静态文件
npm-debug.log*         # npm 日志
```

### 应该提交的文件

- ✅ `frontend/package.json`
- ✅ `frontend/package-lock.json`（重要！）
- ✅ `frontend/.npmrc`（如果有）
- ✅ `pyproject.toml`
- ✅ `uv.lock`（如果使用 uv）

### 不应该提交的文件

- ❌ `node_modules/`
- ❌ `frontend/dist/`
- ❌ `static/dist/`
- ❌ `*.log`

## CI/CD 构建

GitHub Actions 会自动：

1. 使用 `npm ci` 安装前端依赖（需要 package-lock.json）
2. 构建前端到 `static/dist/`
3. 使用 `pip install -e .` 安装 Python 依赖
4. 打包桌面应用

## 故障排除

### 前端依赖安装失败

```bash
# 清除缓存和依赖
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

### 依赖版本冲突

检查 `package-lock.json` 是否已提交到 Git。如果缺失，运行：

```bash
cd frontend
npm install  # 生成 package-lock.json
cd ..
git add frontend/package-lock.json
git commit -m "Add package-lock.json"
```

### 构建时找不到依赖

确保：
1. `package-lock.json` 已提交到 Git
2. 使用 `npm ci` 而不是 `npm install` 进行构建
3. Node.js 版本 >= 16.0.0
