# 开发工具脚本

## 快速修复脚本

```bash
# 系统检查
./scripts/quick-fix.sh check

# 重置数据库
./scripts/quick-fix.sh db

# 设置暗黑模式
./scripts/quick-fix.sh theme

# 清理缓存并重启
./scripts/quick-fix.sh cache

# 运行所有修复
./scripts/quick-fix.sh all
```

## 调试脚本

```bash
# 使用模板调试
node scripts/debug-template.js
```

## 常用调试命令

```bash
# 截图验证
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/" screenshots/test.png

# 查看数据库
sqlite3 ~/Library/Application\ Support/anime1-desktop-electron/anime1.db \
  "SELECT * FROM settings;"

# 查看日志
tail -f ~/Library/Application\ Support/anime1-desktop-electron/logs/main.log
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 暗黑模式不生效 | `./scripts/quick-fix.sh theme` |
| 收藏显示异常 | 检查 `favorite.ts` 中的 `isFavorite` getter |
| 页面白屏 | 检查主进程日志，重启应用 |
| 数据库锁定 | 关闭应用后删除 `instance.lock` |
