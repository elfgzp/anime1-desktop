# SQLite 替代方案对比（2025-2026）

## 推荐方案：libsql-js

**GitHub**: https://github.com/tursodatabase/libsql-js

### 优势

| 特性 | better-sqlite3 | libsql-js |
|------|---------------|-----------|
| 维护状态 | ⚠️ 滞后 | ✅ 非常活跃 |
| 最后更新 | 2024 | **2025年11月** |
| Node.js 24 | ❌ 不支持 | ✅ 支持 |
| API 兼容 | - | ✅ 兼容 better-sqlite3 |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐ |
| 后台 | C++ | Rust (napi-rs) |
| 社区 | 一般 | 非常活跃 (13k+ stars) |

### 安装

```bash
npm install libsql
```

### 代码迁移

几乎**零改动**！API 完全兼容：

```typescript
// 之前 (better-sqlite3)
import Database from 'better-sqlite3'
const db = new Database('anime1.db')

// 之后 (libsql-js)
import { Database } from 'libsql'
const db = new Database('anime1.db')
// 其他代码完全不用改！
```

## 备选方案

### 1. node-sqlite3-wasm
- **优点**: 纯 WASM，无需编译，任何 Node.js 版本都支持
- **缺点**: 性能稍差
- **适合**: 不想处理任何编译问题

```bash
npm install node-sqlite3-wasm
```

### 2. 继续使用 better-sqlite3
- **方法**: 锁定 Node.js 20 LTS
- **缺点**: 长期维护麻烦

## 建议

**推荐用 libsql-js 替换 better-sqlite3**：
1. 迁移成本几乎为零（API 兼容）
2. 维护积极，跟进 Node.js 更新快
3. Turso 团队背书，长期有保障
4. 性能一样好

## 迁移步骤

```bash
# 1. 卸载旧依赖
npm uninstall better-sqlite3

# 2. 安装新依赖
npm install libsql

# 3. 修改导入语句
# 从: import Database from 'better-sqlite3'
# 改为: import { Database } from 'libsql'

# 4. 其他代码完全不用改！
```
