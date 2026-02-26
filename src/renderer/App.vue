<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { onMounted } from 'vue'
import { useSettingsStore } from './stores'

const settingsStore = useSettingsStore()

// 初始化主题
onMounted(async () => {
  // 先加载设置
  await settingsStore.loadSettings()
  // 应用主题（主题会在 loadSettings 中自动应用）
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  overflow-y: auto;
  background-color: var(--el-bg-color-page, #f2f3f5);
}

html {
  overflow-x: hidden;
  overflow-y: auto;
}

#app {
  min-height: 100vh;
}

/* 主题变量 - 覆盖 Element Plus 默认主题 */
:root {
  /* Element Plus 主色调 */
  --el-color-primary: #7c5cff;
  --el-color-primary-light-3: #9c8aff;
  --el-color-primary-light-5: #b5adff;
  --el-color-primary-light-7: #d0ccff;
  --el-color-primary-light-8: #e0ddff;
  --el-color-primary-light-9: #f0eeff;
  --el-color-primary-dark-2: #6a4fd6;
  
  /* Anime 主题变量 */
  --anime-primary: #7c5cff;
  --anime-primary-hover: #6a4fd6;
  --anime-secondary: #ff6b9d;
  --anime-bg-dark: #1a1a2e;
  --anime-bg-card: #252542;
  --anime-bg-hover: #2d2d4a;
}

/* 亮色模式 */
html.light {
  --anime-bg-card: #ffffff;
  --anime-bg-hover: #f5f5fa;
  --el-fill-color-light: #f5f5fa;
  --el-bg-color: #ffffff;
  --el-border-color: #e0e0e6;
}

/* 暗色模式 */
html.dark {
  --anime-bg-card: #252542;
  --anime-bg-hover: #2d2d4a;
  --el-fill-color-light: #252542;
  --el-bg-color: #1a1a2e;
  --el-border-color: #3d3d5c;
}

/* Element Plus 统一样式 */
.el-button--primary {
  --el-button-bg-color: #7c5cff;
  --el-button-border-color: #7c5cff;
  --el-button-hover-bg-color: #6a4fd6;
  --el-button-hover-border-color: #6a4fd6;
  --el-button-active-bg-color: #5a3fc6;
  --el-button-active-border-color: #5a3fc6;
}

.el-button--primary.is-plain {
  --el-button-bg-color: rgba(124, 92, 255, 0.1);
  --el-button-border-color: #7c5cff;
  --el-button-hover-bg-color: rgba(124, 92, 255, 0.2);
  --el-button-hover-border-color: #7c5cff;
  --el-button-text-color: #7c5cff;
}

/* 输入框样式 */
.el-input__wrapper {
  background-color: var(--el-fill-color-light);
  box-shadow: none !important;
  border: 1px solid var(--el-border-color);
  transition: all 0.2s;
}

.el-input__wrapper:hover {
  border-color: #7c5cff;
}

.el-input__wrapper.is-focus {
  border-color: #7c5cff;
  box-shadow: 0 0 0 1px #7c5cff !important;
}

.el-input__inner {
  color: var(--el-text-color-primary) !important;
}

/* Card 样式 */
.el-card {
  --el-card-bg-color: var(--el-bg-color);
  border-radius: 12px;
}

/* Tag 样式 */
.el-tag {
  border-radius: 6px;
}

/* 分页器样式 */
.el-pagination .el-pager li {
  background-color: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}

.el-pagination .el-pager li:hover {
  color: #7c5cff;
}

.el-pagination .el-pager li.is-active {
  background-color: #7c5cff;
  color: #fff;
}

.el-pagination button:hover {
  color: #7c5cff;
}

/* 骨架屏样式 */
.el-skeleton {
  --el-skeleton-color: rgba(124, 92, 255, 0.1);
  --el-skeleton-to-color: rgba(124, 92, 255, 0.2);
}

/* 链接样式 */
.el-link--primary {
  --el-link-text-color: #7c5cff;
}

.el-link--primary:hover {
  color: #6a4fd6;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(124, 92, 255, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(124, 92, 255, 0.5);
}
</style>
