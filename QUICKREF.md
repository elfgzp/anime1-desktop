# 快速参考卡片

## 启动应用
```bash
npm run dev
```

## 调试检查
```bash
# 系统检查
./scripts/quick-fix.sh check

# 截图验证
npx playwright screenshot --browser=chromium \
  "http://localhost:5173/" screenshots/test.png
```

## 常见问题修复

### 暗黑模式不生效
```bash
./scripts/quick-fix.sh theme
```

### 收藏按钮异常
检查 `Home.vue`:
```typescript
function isAnimeFavorite(animeId: string): boolean {
  try {
    return favoritesStore.isFavorite(animeId)
  } catch {
    return false
  }
}
```

### 数据问题
```bash
# 重置数据库
./scripts/quick-fix.sh db

# 手动插入设置
sqlite3 ~/Library/Application\ Support/anime1-desktop-electron/anime1.db \
  "INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', '\"dark\"');"
```

## 关键文件位置

| 类型 | 路径 |
|------|------|
| 主进程入口 | `src/main/index.ts` |
| IPC 处理 | `src/main/ipc/index.ts` |
| Vue 入口 | `src/renderer/main.ts` |
| 路由 | `src/renderer/router/index.ts` |
| Store | `src/renderer/stores/` |
| 数据库 | `~/Library/Application Support/anime1-desktop-electron/anime1.db` |
| 日志 | `~/Library/Application Support/anime1-desktop-electron/logs/main.log` |

## API 调试

```javascript
// 在主进程中测试
const result = await page.evaluate(async () => {
  return await window.api.anime.getList({ page: 1 });
});
```

## 数据库表结构

```sql
-- 收藏
CREATE TABLE favorite_anime (
  anime_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  detail_url TEXT NOT NULL,
  episode INTEGER,
  cover_url TEXT,
  year TEXT,
  season TEXT,
  subtitle_group TEXT,
  last_episode INTEGER DEFAULT 0,
  added_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- 设置
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

## IPC 命名规范

- `anime:list` - 获取番剧列表
- `anime:detail` - 获取番剧详情
- `favorite:list` - 获取收藏列表
- `favorite:add` - 添加收藏
- `settings:getAll` - 获取所有设置
- `settings:set` - 保存设置

## 开发 checklist

- [ ] 运行 `./scripts/quick-fix.sh check` 确认环境正常
- [ ] 截图验证 UI 显示正确
- [ ] 测试暗黑模式切换和持久化
- [ ] 测试收藏功能（添加/删除/显示）
- [ ] 检查主进程日志无错误
