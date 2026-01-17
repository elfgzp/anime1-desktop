<template>
  <div class="layout-container" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '240px'" class="sidebar">
      <div class="sidebar-header">
        <h1 v-if="!sidebarCollapsed" class="sidebar-title">Anime1</h1>
        <span v-else class="sidebar-logo">A1</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
      >
        <el-menu-item :index="ROUTES.HOME">
          <el-icon><VideoPlay /></el-icon>
          <template #title>最新番剧</template>
        </el-menu-item>

        <el-menu-item :index="ROUTES.FAVORITES">
          <el-icon><Star /></el-icon>
          <template #title>我的追番</template>
          <el-badge
            v-if="favoritesBadge"
            :value="''"
            class="sidebar-badge"
            :hidden="!favoritesBadge"
          />
        </el-menu-item>

        <el-menu-item :index="ROUTES.PLAYBACK">
          <el-icon><Clock /></el-icon>
          <template #title>观看历史</template>
        </el-menu-item>

        <el-menu-item :index="ROUTES.SETTINGS">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button
          :icon="sidebarCollapsed ? Expand : Fold"
          circle
          size="small"
          @click="toggleSidebar"
          class="collapse-btn"
        />
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { VideoPlay, Star, Clock, Setting, Expand, Fold } from '@element-plus/icons-vue'
import { updateAPI, favoriteAPI } from '../utils/api'
import { ROUTES } from '../constants/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const sidebarCollapsed = ref(true)  // 默认收缩，只显示 logo
const updateBadge = ref(false)
const favoritesBadge = ref(false)

const activeMenu = computed(() => {
  const path = route.path
  // 检查是否是番剧详情页
  if (path.startsWith('/anime/')) {
    return ROUTES.HOME
  }
  return path
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  // 保存到 localStorage
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value.toString())
}

const checkUpdate = async (showModal = false) => {
  try {
    const response = await updateAPI.check()
    if (response.data.has_update) {
      updateBadge.value = true
      if (showModal) {
        // TODO: 显示更新弹窗
        ElMessage.info(`发现新版本: ${response.data.latest_version}`)
      }
    } else {
      updateBadge.value = false
    }
  } catch (error) {
    console.error('检查更新失败:', error)
  }
}

const checkFavoritesUpdates = async () => {
  try {
    const response = await favoriteAPI.checkUpdates()
    if (response.data.success && response.data.has_updates) {
      favoritesBadge.value = true
    } else {
      favoritesBadge.value = false
    }
  } catch (error) {
    console.error('检查追番更新失败:', error)
  }
}

onMounted(() => {
  // 从 localStorage 恢复侧边栏状态
  const saved = localStorage.getItem('sidebarCollapsed')
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true'
  }
  
  // 检查更新
  checkUpdate()
  checkFavoritesUpdates()
  
  // 定期检查更新
  setInterval(() => {
    checkUpdate()
    checkFavoritesUpdates()
  }, 300000) // 5分钟检查一次
})
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60px;
}

.sidebar-title {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ff6b9d 0%, #7c5cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.sidebar-logo {
  font-size: 1rem;
  font-weight: 700;
  background: linear-gradient(135deg, #ff6b9d 0%, #7c5cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
}

.sidebar-badge {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid var(--el-border-color);
  display: flex;
  justify-content: center;
}

.collapse-btn {
  width: 32px;
  height: 32px;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 0;
  transition: margin-left 0.3s;
}

.main-content {
  flex: 1;
  padding: 20px;
  background: var(--el-bg-color-page);
  overflow-y: auto;
  min-width: 0;
}

/* 暗色主题适配 */
:deep(.el-menu-item) {
  color: var(--el-text-color-regular);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.15) 0%, rgba(124, 92, 255, 0.15) 100%);
  color: var(--el-color-primary);
  border-left: 3px solid var(--el-color-primary);
}

:deep(.el-menu-item:hover) {
  background: var(--el-fill-color-light);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(0);
  }

  .sidebar-collapsed .sidebar {
    transform: translateX(-100%);
  }

  .main-container {
    margin-left: 0;
  }
}
</style>
