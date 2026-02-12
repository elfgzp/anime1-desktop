# Node.js 版本问题说明

## 问题原因

### 1. 这不是方案的问题
Electron + TypeScript + Vue 的架构是**主流且成熟**的方案，Discord、Slack、VS Code 都是这个架构。

### 2. 真正的原因：better-sqlite3 原生模块

```
你的错误：use of undeclared identifier 'requires'
```

这个错误来自 **better-sqlite3**（SQLite 的 Node.js 绑定），这是一个**原生 C++ 模块**。

### 3. 什么是原生模块？

```
JavaScript/TypeScript 代码
    ↓
Node.js (V8 引擎)
    ↓
原生模块 (C/C++)
    ↓
系统调用 (SQLite/文件系统/网络)
```

原生模块需要用 **node-gyp** 编译成二进制文件，这个过程依赖：
- Node.js 的 C++ API
- 系统编译器 (gcc/clang/MSVC)

### 4. 为什么 Node.js 24 不行？

Node.js 24 是 **2025年4月** 才发布的非常新的版本：

| 版本 | 发布日期 | 状态 |
|------|---------|------|
| Node.js 18 | 2022年4月 | LTS (维护中) |
| Node.js 20 | 2023年4月 | LTS (推荐) |
| Node.js 22 | 2024年4月 | LTS |
| **Node.js 24** | **2025年4月** | **Current (非常新)** |

**better-sqlite3** 的作者还没来得及适配 Node.js 24 的 C++ API 变化。

### 5. C++ 错误详情

```cpp
// Node.js 24 引入了 C++20 的 concept/requires 语法
// 但 better-sqlite3 的编译配置还没跟上
concept RequiresStackAllocated =
    requires { typename T::IsStackAllocatedTypeMarker; };
// ^^^^^^^ 编译器不认识这个关键字
```

## 解决方案

### 方案 1：使用 Node.js 20 LTS（推荐）

```bash
# 安装 LTS 版本
nvm install 20
nvm use 20

# 删除旧的 node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 方案 2：使用预编译版本（避免编译）

```bash
# better-sqlite3 提供预编译的二进制包
npm install better-sqlite3 --build-from-source=false
```

### 方案 3：等待 better-sqlite3 更新

```bash
# 关注 better-sqlite3 的更新
npm info better-sqlite3
```

## 为什么原项目没有这个问题？

原项目用 Python，**Python 的 SQLite 是标准库**：

```python
# Python 内置，无需额外编译
import sqlite3
```

Node.js 没有内置 SQLite，所以需要第三方库，而 better-sqlite3 是**性能最好**的选择（纯 JS 的 sqlite3 包很慢）。

## 替代方案（如果不想降级 Node.js）

### 方案 A：使用 better-sqlite3 的替代库

| 库 | 类型 | 性能 | 备注 |
|-----|------|------|------|
| **better-sqlite3** | 原生 | ⭐⭐⭐ | 目前用的，需要编译 |
| sqlite3 | 原生 | ⭐⭐ | 也需要编译 |
| **@libsql/client** | 原生 | ⭐⭐⭐ | Turso 出品，更新快 |
| **node-sqlite3-wasm** | WASM | ⭐⭐ | 无需编译，兼容性好 |

如果想用 Node.js 24，可以换成 `node-sqlite3-wasm`：

```bash
npm uninstall better-sqlite3
npm install node-sqlite3-wasm
```

### 方案 B：使用更简单的存储

如果只是配置存储，可以用 **electron-store**（纯 JSON）：

```typescript
import Store from 'electron-store'

// 不用 SQLite，用 JSON 文件
const store = new Store()
store.set('favorites', [...])
```

## 总结

| 问题 | 答案 |
|------|------|
| 方案有问题吗？ | ❌ 没有，Electron + TS 是行业标准 |
| 谁的问题？ | better-sqlite3 还没适配 Node.js 24 |
| 怎么解决？ | 用 Node.js 20 LTS（稳定） |
| 长期方案？ | 等 better-sqlite3 更新，或换 WASM 版本 |

**推荐使用 Node.js 20 LTS**，这是目前最稳定的版本，几乎所有库都支持。
