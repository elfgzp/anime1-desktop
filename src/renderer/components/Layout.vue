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
        <el-menu-item index="/" data-testid="menu-home">
          <el-icon><VideoPlay /></el-icon>
          <template #title>最新番剧</template>
        </el-menu-item>

        <el-menu-item index="/favorites" data-testid="menu-favorites">
          <el-icon><Star /></el-icon>
          <template #title>我的追番</template>
          <el-badge
            v-if="favoritesStore.hasUpdates"
            :value="''"
            class="sidebar-badge"
            :hidden="!favoritesStore.hasUpdates"
          />
        </el-menu-item>

        <el-menu-item index="/history" data-testid="menu-history">
          <el-icon><Clock /></el-icon>
          <template #title>观看历史</template>
        </el-menu-item>

        <el-menu-item index="/downloads" data-testid="menu-downloads">
          <el-icon><Download /></el-icon>
          <template #title>下载管理</template>
        </el-menu-item>

        <el-menu-item index="/settings" data-testid="menu-settings">
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

    <!-- 更新弹窗 -->
    <el-dialog
      v-model="updateDialogVisible"
      title="发现新版本"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="update-dialog-header">
        <el-icon color="#67c23a" size="20"><CircleCheckFilled /></el-icon>
        <span style="margin-left: 8px;">发现新版本</span>
        <el-tag v-if="updateInfo.isPrelease" type="warning" size="small" style="margin-left: 8px;">预发布</el-tag>
      </div>
      <div class="update-dialog-content">
        <div class="version-info">
          <p><strong>当前版本:</strong> {{ updateInfo.currentVersion || '-' }}</p>
          <p><strong>最新版本:</strong> {{ updateInfo.latestVersion || '-' }}</p>
        </div>
        <el-divider />
        <div class="release-notes" v-html="formatReleaseNotes(updateInfo.releaseNotes)"></div>
      </div>
      <template #footer>
        <el-button @click="updateDialogVisible = false">暂不更新</el-button>
        <el-button type="primary" @click="handleDownloadUpdate" :loading="downloading">
          {{ downloading ? '下载中...' : '下载更新' }}
          <el-icon v-if="!downloading" style="margin-left: 4px;"><Download /></el-icon>
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { VideoPlay, Star, Clock, Setting, Expand, Fold, CircleCheckFilled, Download } from '@element-plus/icons-vue'
import { useFavoritesStore } from '../stores'
import { ElMessage } from 'element-plus'

const route = useRoute()
const favoritesStore = useFavoritesStore()

const sidebarCollapsed = ref(true)
const updateDialogVisible = ref(false)
const downloading = ref(false)

const updateInfo = ref({
  latestVersion: '',
  currentVersion: '',
  downloadUrl: '',
  releaseNotes: '',
  isPrelease: false
})

// 当前激活的菜单
const activeMenu = computed(() => {
  const path = route.path
  // 番剧详情页高亮首页
  if (path.startsWith('/anime/')) {
    return '/'
  }
  return path
})

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar-collapsed', sidebarCollapsed.value.toString())
}

// 格式化更新日志
const formatReleaseNotes = (notes: string) => {
  if (!notes) return '<p style="color: #909399;">暂无更新说明</p>'
  const html = notes
    .replace(/\n/g, '<br>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #4ecdc4;">$1</a>')
  return html || '<p style="color: #909399;">暂无更新说明</p>'
}

// 检查更新
const checkUpdate = async (showModal = false) => {
  try {
    const result = await window.api.update.check()
    if (result.success && result.data) {
      const { hasUpdate, latestVersion, currentVersion, downloadUrl, releaseNotes, isPrelease } = result.data
      if (hasUpdate) {
        updateInfo.value = {
          latestVersion,
          currentVersion,
          downloadUrl: downloadUrl || '',
          releaseNotes: releaseNotes || '',
          isPrelease: isPrelease || false
        }
        if (showModal) {
          updateDialogVisible.value = true
        }
      }
    }
  } catch (error) {
    console.error('[更新检查] 失败:', error)
  }
}

// 下载更新
const handleDownloadUpdate = async () => {
  if (!updateInfo.value.downloadUrl) {
    ElMessage.error('下载链接不可用')
    return
  }
  
  downloading.value = true
  try {
    await window.api.system.openExternal({ url: updateInfo.value.downloadUrl })
    updateDialogVisible.value = false
  } catch (error) {
    ElMessage.error('打开下载链接失败')
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  // 恢复侧边栏状态
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true'
  }
  
  // 检查更新
  checkUpdate()
  
  // 加载收藏（检查更新徽章）
  favoritesStore.loadFavorites()
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
  min-width: 0;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 0;
  background: var(--el-bg-color-page);
  overflow-y: auto;
  min-width: 0;
}

/* 菜单样式 */
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

/* 更新弹窗样式 */
.update-dialog-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.update-dialog-content {
  padding: 0 10px;
}

.version-info {
  margin-bottom: 8px;
}

.version-info p {
  margin: 4px 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.release-notes {
  max-height: 200px;
  overflow-y: auto;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.release-notes a {
  color: #4ecdc4;
  text-decoration: none;
}

.release-notes a:hover {
  text-decoration: underline;
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
