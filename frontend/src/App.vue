<template>
  <el-config-provider :locale="locale">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useThemeStore } from './composables/useTheme'

const themeStore = useThemeStore()

const locale = computed(() => zhCn)
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
  overflow-y: auto; /* 确保滚动正常 */
}

html {
  overflow-x: hidden;
  overflow-y: auto;
}

#app {
  min-height: 100vh;
  overflow: visible;
}

/* 统一按钮风格 - 参考 Anime1 */
:root {
  --anime-primary: #7c5cff;
  --anime-primary-hover: #6a4fd6;
  --anime-secondary: #ff6b9d;
  --anime-bg-dark: #1a1a2e;
  --anime-bg-card: #252542;
  --anime-bg-hover: #2d2d4a;
}

/* 亮色模式配色覆盖 */
html.light {
  --anime-bg-card: #ffffff;
  --anime-bg-hover: #f5f5fa;
  --el-fill-color-light: #f5f5fa;
  --el-bg-color: #ffffff;
  --el-border-color: #e0e0e6;
}

/* 暗色模式配色覆盖 */
html.dark {
  --anime-bg-card: #252542;
  --anime-bg-hover: #2d2d4a;
  --el-fill-color-light: #252542;
  --el-bg-color: #1a1a2e;
  --el-border-color: #3d3d5c;
}

/* Element Plus 按钮统一样式 */
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

/* 输入框统一样式 */
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

/* 搜索框特殊样式 */
.search-input .el-input__wrapper {
  background-color: var(--el-bg-color);
}

/* Select 下拉框统一样式 */
.el-select .el-input__wrapper {
  background-color: var(--el-fill-color-light);
}

.el-select-dropdown {
  background-color: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.el-select-dropdown__item {
  color: var(--el-text-color-primary);
}

.el-select-dropdown__item:hover {
  background-color: rgba(124, 92, 255, 0.1);
}

.el-select-dropdown__item.is-selected {
  color: #7c5cff;
  background-color: rgba(124, 92, 255, 0.1);
}

/* Card 统一样式 */
.el-card {
  --el-card-bg-color: var(--el-bg-color);
  border-radius: 12px;
}

/* Tag 统一样式 */
.el-tag {
  border-radius: 6px;
}

/* 分页器统一样式 */
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

/* 空状态统一样式 */
.el-empty__description p {
  color: var(--el-text-color-secondary);
}

/* 骨架屏统一样式 */
.el-skeleton {
  --el-skeleton-color: rgba(124, 92, 255, 0.1);
  --el-skeleton-to-color: rgba(124, 92, 255, 0.2);
}

/* 链接统一样式 */
.el-link--primary {
  --el-link-text-color: #7c5cff;
}

.el-link--primary:hover {
  color: #6a4fd6;
}
</style>
