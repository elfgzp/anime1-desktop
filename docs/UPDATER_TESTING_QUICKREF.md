# 自动更新 Mock 测试 - 快速参考

## 🚀 一行命令启动测试

```bash
# 默认场景：有更新
./scripts/test-updater.sh

# 指定场景
./scripts/test-updater.sh no-update
./scripts/test-updater.sh has-update
./scripts/test-updater.sh check-error
./scripts/test-updater.sh download-error
./scripts/test-updater.sh downloaded

# 打开 DevTools
./scripts/test-updater.sh --devtools has-update

# 运行单元测试
./scripts/test-updater.sh --test
```

## 🎮 可用场景速查

| 场景 | 命令 | 用途 |
|------|------|------|
| **无更新** | `no-update` | 测试"已是最新"提示 |
| **有更新** | `has-update` | 测试完整更新流程 |
| **检查失败** | `check-error` | 测试网络错误处理 |
| **下载失败** | `download-error` | 测试下载中断处理 |
| **已下载** | `downloaded` | 测试安装流程 |

## 💻 DevTools 控制台命令

```javascript
// 获取可用场景
await electron.ipcRenderer.invoke('mock-updater:get-scenarios')

// 切换场景
await electron.ipcRenderer.invoke('mock-updater:set-scenario', 'no-update')

// 获取当前状态
await electron.ipcRenderer.invoke('updater:status')

// 检查更新
await electron.ipcRenderer.invoke('updater:check')

// 下载更新
await electron.ipcRenderer.invoke('updater:download')

// 安装更新
await electron.ipcRenderer.invoke('updater:install')

// 重置状态
await electron.ipcRenderer.invoke('mock-updater:reset')
```

## 🔧 环境变量

```bash
# 启用 Mock 模式（必需）
MOCK_UPDATER=true

# 选择场景
MOCK_UPDATER_SCENARIO=has-update

# 设置版本号
MOCK_UPDATER_VERSION=9.9.9

# 设置当前版本（用于对比）
MOCK_CURRENT_VERSION=1.0.0

# 设置检查延迟（毫秒）
MOCK_CHECK_DELAY=2000

# 设置下载延迟（毫秒）
MOCK_DOWNLOAD_DELAY=5000
```

## 🧩 在 Vue 组件中使用

```vue
<script setup>
import { ref, onMounted } from 'vue';
import MockUpdaterPanel from './components/MockUpdaterPanel.vue';

const isMockMode = ref(false);

onMounted(async () => {
  const result = await window.electron.ipcRenderer.invoke('mock-updater:get-config');
  isMockMode.value = result.data?.isMock;
});
</script>

<template>
  <!-- 添加 Mock 控制面板 -->
  <MockUpdaterPanel v-if="isMockMode" />
</template>
```

## 🧪 单元测试

```bash
# 运行测试
npm test -- tests/unit/updater.mock.test.js

# 带覆盖率
npm test -- tests/unit/updater.mock.test.js --coverage

# 调试模式
npm test -- tests/unit/updater.mock.test.js --reporter=verbose
```

## 📊 测试覆盖场景

| 功能 | 测试状态 |
|------|----------|
| 初始化 Mock | ✅ |
| 场景切换 | ✅ |
| 检查更新 - 无更新 | ✅ |
| 检查更新 - 有更新 | ✅ |
| 检查更新 - 网络错误 | ✅ |
| 下载更新 - 正常 | ✅ |
| 下载更新 - 失败 | ✅ |
| 安装更新 | ✅ |
| 状态查询 | ✅ |
| 事件监听 | ✅ |

## 🔗 相关文件

```
src/
├── services/
│   ├── updater.js           # 主文件（包含 Mock 集成）
│   └── updater.mock.js      # Mock 实现
└── renderer/components/
    └── MockUpdaterPanel.vue # 测试控制面板 UI

tests/unit/
└── updater.mock.test.js     # 单元测试

scripts/
└── test-updater.sh          # 测试脚本

docs/
├── UPDATER_TESTING.md       # 完整文档
└── UPDATER_TESTING_QUICKREF.md  # 快速参考（本文档）
```

## 💡 常见问题

### Q: 如何判断当前是否在 Mock 模式？
```javascript
const result = await window.electron.ipcRenderer.invoke('mock-updater:get-config');
if (result.data?.isMock) {
  console.log('当前是 Mock 模式');
}
```

### Q: Mock 模式会影响正式版本吗？
不会。需要显式设置 `MOCK_UPDATER=true` 才会启用。

### Q: 可以在 E2E 测试中使用吗？
可以：
```javascript
const electronApp = await electron.launch({
  args: ['.'],
  env: {
    ...process.env,
    MOCK_UPDATER: 'true',
    MOCK_UPDATER_SCENARIO: 'has-update',
  },
});
```

### Q: 如何自定义模拟版本号？
```bash
MOCK_UPDATER=true MOCK_UPDATER_VERSION=5.5.5 npm start
```

## 📚 详细文档

- [完整测试指南](./UPDATER_TESTING.md)
- [CI/CD 架构文档](./CICD.md)
- [构建指南](../BUILD.md)
