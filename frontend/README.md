# Frontend

Vue 3 前端应用，使用 Vite 构建。

## 依赖管理

### 安装依赖

```bash
# 首次安装（会生成 package-lock.json）
npm install

# 生产构建（使用 package-lock.json，更快且更可靠）
npm ci
```

### 依赖文件

- `package.json` - 依赖声明（已提交到 Git）
- `package-lock.json` - 锁定依赖版本（已提交到 Git，确保构建一致性）
- `node_modules/` - 依赖安装目录（已添加到 .gitignore）

## 开发

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 构建输出

构建产物输出到 `../static/dist/` 目录，供 Flask 后端使用。

## 注意事项

- `package-lock.json` 必须提交到 Git，确保依赖版本一致性
- 使用 `npm ci` 进行 CI/CD 构建，而不是 `npm install`
- Node.js 版本要求 >= 16.0.0
