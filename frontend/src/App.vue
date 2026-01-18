<template>
  <el-config-provider :locale="locale">
    <router-view />
    <!-- 鼠标侧键提示 Toast -->
    <Transition name="toast-fade">
      <div v-if="sidebarToast.show" class="sidebar-toast">
        {{ sidebarToast.message }}
      </div>
    </Transition>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useThemeStore } from './composables/useTheme'
import { reportAllMetrics } from './utils/performance'

const themeStore = useThemeStore()

const locale = computed(() => zhCn)

// 鼠标侧键 toast 状态
const sidebarToast = reactive({
  show: false,
  message: ''
})

let toastTimer = null

const showSidebarToast = (message) => {
  sidebarToast.message = message
  sidebarToast.show = true

  // 清除之前的定时器
  if (toastTimer) {
    clearTimeout(toastTimer)
  }

  // 1.5秒后自动隐藏
  toastTimer = setTimeout(() => {
    sidebarToast.show = false
  }, 1500)
}

const handleMouseDown = (e) => {
  // button 3 = 后退键, button 4 = 前进键
  if (e.button === 3) {
    e.preventDefault()
    showSidebarToast('← 点击了后退键')
  } else if (e.button === 4) {
    e.preventDefault()
    showSidebarToast('点击了前进键 →')
  }
}

// 上报 Core Web Vitals
onMounted(() => {
  // 延迟上报，确保后端服务已启动
  setTimeout(() => {
    reportAllMetrics()
  }, 2000)

  // 监听鼠标侧键
  window.addEventListener('mousedown', handleMouseDown)
})

onUnmounted(() => {
  window.removeEventListener('mousedown', handleMouseDown)
  if (toastTimer) {
    clearTimeout(toastTimer)
  }
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

/* 鼠标侧键提示 Toast */
.sidebar-toast {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  background-color: rgba(124, 92, 255, 0.85);
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.3);
  pointer-events: none;
  backdrop-filter: blur(8px);
}

/* 暗色模式 toast */
html.dark .sidebar-toast {
  background-color: rgba(124, 92, 255, 0.9);
}

/* 亮色模式 toast */
html.light .sidebar-toast {
  background-color: rgba(124, 92, 255, 0.9);
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.2);
}

/* Toast 动画 */
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}
</style>
