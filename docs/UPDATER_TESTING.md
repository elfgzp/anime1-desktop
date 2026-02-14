# 自动更新功能 Mock 测试指南

## 概述

为了让自动更新功能的测试更加便捷，我们提供了完整的 **Mock 测试方案**。无需真实发布到 GitHub Releases，即可模拟各种更新场景。

## 快速开始

### 1. 启用 Mock 模式

```bash
# 设置环境变量
export MOCK_UPDATER=true

# 可选：设置测试场景
export MOCK_UPDATER_SCENARIO=has-update

# 可选：设置模拟版本号
export MOCK_UPDATER_VERSION=9.9.9

# 启动应用
npm start
```

### 2. 命令行快捷启动

```bash
# Linux/macOS
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=has-update npm start

# Windows PowerShell
$env:MOCK_UPDATER="true"; $env:MOCK_UPDATER_SCENARIO="has-update"; npm start

# Windows CMD
set MOCK_UPDATER=true && set MOCK_UPDATER_SCENARIO=has-update && npm start
```

## 可用的测试场景

| 场景 | 环境变量值 | 说明 |
|------|-----------|------|
| **无更新** | `no-update` | 模拟已是最新版本 |
| **有更新** | `has-update` | 模拟发现新版本 v9.9.9（默认） |
| **检查错误** | `check-error` | 模拟网络错误，无法检查更新 |
| **下载错误** | `download-error` | 模拟下载到 50% 时失败 |
| **已下载** | `downloaded` | 模拟更新已下载，等待安装 |

## 测试场景详解

### 场景 1: 无更新 (no-update)

```bash
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=no-update npm start
```

**预期行为:**
- 检查更新后显示"已是最新版本"
- 不触发下载流程

**适用测试:**
- 检查更新 UI 显示
- 确认无更新时的提示信息

### 场景 2: 有更新 (has-update) - 默认

```bash
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=has-update npm start
```

**预期行为:**
- 检测到新版本 v9.9.9
- 显示更新详情（版本号、更新日志、文件大小）
- 可触发下载并看到进度条
- 下载完成后可安装

**适用测试:**
- 完整更新流程
- 进度条显示
- 更新提示 UI

### 场景 3: 检查错误 (check-error)

```bash
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=check-error npm start
```

**预期行为:**
- 检查更新时显示错误提示
- 错误信息："无法连接到更新服务器，请检查网络连接"

**适用测试:**
- 错误提示 UI
- 网络错误处理
- 重试机制

### 场景 4: 下载错误 (download-error)

```bash
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=download-error npm start
```

**预期行为:**
- 正常检测到更新
- 开始下载并显示进度
- 在 50% 时显示下载失败
- 错误信息："下载更新失败：磁盘空间不足"

**适用测试:**
- 下载中断处理
- 错误恢复机制
- 部分下载状态

### 场景 5: 已下载 (downloaded)

```bash
MOCK_UPDATER=true MOCK_UPDATER_SCENARIO=downloaded npm start
```

**预期行为:**
- 检查更新后立即显示"更新已下载"
- 可直接触发安装

**适用测试:**
- 安装流程
- 应用重启逻辑

## 开发者工具

### 通过 DevTools 控制台控制

在应用启动后，打开 DevTools 控制台，使用以下 API：

```javascript
// 获取当前配置
await electron.ipcRenderer.invoke('mock-updater:get-config')
// 返回: { success: true, data: { isMock: true, scenario: 'has-update', ... } }

// 获取可用场景列表
await electron.ipcRenderer.invoke('mock-updater:get-scenarios')
// 返回: { success: true, data: [{ id, name, description }, ...] }

// 切换场景（无需重启）
await electron.ipcRenderer.invoke('mock-updater:set-scenario', 'download-error')
// 返回: { success: true, scenario: 'download-error' }

// 获取当前状态
await electron.ipcRenderer.invoke('updater:status')
// 返回: { success: true, data: { checking, available, downloading, downloaded, progress, ... } }

// 重置状态
await electron.ipcRenderer.invoke('mock-updater:reset')
// 返回: { success: true, state: { ... } }

// 手动触发事件
await electron.ipcRenderer.invoke('mock-updater:trigger-event', {
  eventName: 'available',
  data: { version: '2.0.0', releaseNotes: 'Test' }
})
```

### 测试流程示例

```javascript
// 1. 检查当前场景
await electron.ipcRenderer.invoke('mock-updater:get-config')

// 2. 切换到"有更新"场景
await electron.ipcRenderer.invoke('mock-updater:set-scenario', 'has-update')

// 3. 触发检查更新（通过 UI 或 IPC）
await electron.ipcRenderer.invoke('updater:check')

// 4. 观察 UI 响应，检查状态
await electron.ipcRenderer.invoke('updater:status')

// 5. 下载更新
await electron.ipcRenderer.invoke('updater:download')

// 6. 观察进度，完成后安装
await electron.ipcRenderer.invoke('updater:install')
```

## 单元测试

### 运行测试

```bash
# 运行所有 updater 相关测试
npm test -- tests/unit/updater.mock.test.js

# 运行并查看输出
npm test -- tests/unit/updater.mock.test.js --reporter=verbose
```

### 测试覆盖

测试文件 `tests/unit/updater.mock.test.js` 包含：

- ✅ Mock 初始化
- ✅ IPC 处理器注册
- ✅ 场景切换
- ✅ 检查更新（各种场景）
- ✅ 下载更新
- ✅ 安装更新
- ✅ 状态查询
- ✅ 配置获取
- ✅ 状态重置

## 进阶用法

### 自定义 Mock 配置

通过环境变量调整 Mock 行为：

```bash
# 设置当前版本号（用于对比）
export MOCK_CURRENT_VERSION=1.0.0

# 设置模拟的新版本号
export MOCK_UPDATER_VERSION=2.0.0

# 设置检查延迟（毫秒）
export MOCK_CHECK_DELAY=5000

# 设置下载延迟（毫秒）
export MOCK_DOWNLOAD_DELAY=10000

npm start
```

### 在代码中检测 Mock 模式

```javascript
// 在主进程中检测
import { isMockUpdater } from './services/updater.js';

if (isMockUpdater()) {
  console.log('Running in mock mode');
}
```

```javascript
// 在渲染进程中检测
const config = await electron.ipcRenderer.invoke('mock-updater:get-config');
if (config.data?.isMock) {
  console.log('Mock mode:', config.data.scenario);
}
```

### 渲染进程中的测试 UI

在 Vue 组件中添加测试控制面板：

```vue
<template>
  <div v-if="isMockMode" class="mock-control-panel">
    <h3>🧪 Mock 测试控制</h3>
    <select v-model="currentScenario" @change="changeScenario">
      <option v-for="s in scenarios" :key="s.id" :value="s.id">
        {{ s.name }}
      </option>
    </select>
    <button @click="resetState">重置状态</button>
    <button @click="checkUpdate">检查更新</button>
    <pre>{{ status }}</pre>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const isMockMode = ref(false);
const currentScenario = ref('has-update');
const scenarios = ref([]);
const status = ref({});

onMounted(async () => {
  // 检测是否 Mock 模式
  const config = await window.electron.ipcRenderer.invoke('mock-updater:get-config');
  isMockMode.value = config.data?.isMock;
  
  // 获取可用场景
  const result = await window.electron.ipcRenderer.invoke('mock-updater:get-scenarios');
  scenarios.value = result.data;
});

const changeScenario = async () => {
  await window.electron.ipcRenderer.invoke('mock-updater:set-scenario', currentScenario.value);
};

const resetState = async () => {
  await window.electron.ipcRenderer.invoke('mock-updater:reset');
};

const checkUpdate = async () => {
  await window.electron.ipcRenderer.invoke('updater:check');
};
</script>
```

## 常见问题

### Q: Mock 模式会影响正式版本吗？

不会。Mock 模式仅在设置了 `MOCK_UPDATER=true` 环境变量时启用，正式版本不会受影响。

### Q: 可以模拟特定的版本号吗？

可以。通过 `MOCK_UPDATER_VERSION` 环境变量设置：

```bash
MOCK_UPDATER=true MOCK_UPDATER_VERSION=5.5.5 npm start
```

### Q: 可以调整模拟延迟吗？

可以。修改以下环境变量：

```bash
# 检查更新的延迟（毫秒）
export MOCK_CHECK_DELAY=3000

# 下载的总耗时（毫秒）
export MOCK_DOWNLOAD_DELAY=8000

npm start
```

### Q: 如何在 E2E 测试中使用？

在 Playwright 测试中启动应用时设置环境变量：

```javascript
const { test, expect } = require('@playwright/test');

test('updater flow', async () => {
  const electronApp = await electron.launch({
    args: ['.'],
    env: {
      ...process.env,
      MOCK_UPDATER: 'true',
      MOCK_UPDATER_SCENARIO: 'has-update',
    },
  });
  
  // 测试更新流程...
});
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `src/services/updater.js` | 真实 updater + Mock 集成 |
| `src/services/updater.mock.js` | Mock 实现 |
| `tests/unit/updater.mock.test.js` | 单元测试 |
| `docs/UPDATER_TESTING.md` | 本文档 |

## 总结

使用 Mock 测试可以：

1. **无需真实发布** - 不需要发布到 GitHub Releases
2. **快速迭代** - 即时切换场景，无需等待
3. **覆盖边界情况** - 轻松模拟网络错误、下载中断等
4. **自动化测试** - 可集成到 CI/CD 流程
5. **开发调试** - 实时控制更新流程
