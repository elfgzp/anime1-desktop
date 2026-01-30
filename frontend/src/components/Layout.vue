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

        <el-menu-item :index="'/auto-download'">
          <el-icon><DownloadIcon /></el-icon>
          <template #title>自动下载</template>
        </el-menu-item>

        <!-- 开发者工具（仅开发模式显示） -->
        <el-sub-menu v-if="isDev" index="dev">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>开发者工具</span>
          </template>
          <el-menu-item index="/dev/performance">
            <template #title>性能分析</template>
          </el-menu-item>
        </el-sub-menu>
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
        <el-tag v-if="updateDialogData.is_prerelease" type="warning" size="small" style="margin-left: 8px;">预发布</el-tag>
      </div>
      <div class="update-dialog-content">
        <div class="version-info">
          <p><strong>当前版本:</strong> {{ updateDialogData.current_version || '-' }}</p>
          <p><strong>最新版本:</strong> {{ updateDialogData.latest_version || '-' }}</p>
        </div>
        <el-divider />
        <div class="release-notes" v-html="formatReleaseNotes(updateDialogData.release_notes)"></div>
      </div>
      <template #footer>
        <el-button @click="updateDialogVisible = false">暂不更新</el-button>
        <el-button type="primary" @click="handleDownloadUpdate">
          下载更新
          <el-icon style="margin-left: 4px;"><Download /></el-icon>
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { VideoPlay, Star, Clock, Setting, Expand, Fold, Monitor, CircleCheckFilled, Download, Download as DownloadIcon } from '@element-plus/icons-vue'
import { updateAPI, favoriteAPI } from '../utils/api'
import { ROUTES } from '../constants/api'
import { ElMessage } from 'element-plus'

// 开发模式检测
const isDev = computed(() => import.meta.env.DEV || window.location.port === '5173')

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
  // 检查是否是开发者工具页
  if (path.startsWith('/dev/')) {
    return path
  }
  return path
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  // 保存到 localStorage
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value.toString())
}

// 更新弹窗相关
const updateDialogVisible = ref(false)
const updateDialogData = ref({
  latest_version: '',
  current_version: '',
  download_url: '',
  asset_name: '',
  download_size: '',
  release_notes: '',
  is_prerelease: false
})

const showUpdateDialog = (data) => {
  console.log('[更新弹窗] 显示弹窗，数据:', data)
  updateDialogData.value = {
    latest_version: data.latest_version || '',
    current_version: data.current_version || '',
    download_url: data.download_url || '',
    asset_name: data.asset_name || '',
    download_size: data.download_size || '',
    release_notes: data.release_notes || '',
    is_prerelease: data.is_prerelease || false
  }
  updateDialogVisible.value = true
}

const handleDownloadUpdate = () => {
  const url = updateDialogData.value.download_url
  if (url) {
    console.log('[更新弹窗] 打开下载链接:', url)
    window.open(url, '_blank')
    updateDialogVisible.value = false
  } else {
    ElMessage.error('下载链接不可用')
  }
}

// 格式化 release notes（将 markdown 链接转换为 HTML）
const formatReleaseNotes = (notes) => {
  if (!notes) return '<p style="color: #909399;">暂无更新说明</p>'
  const html = notes
    .replace(/\n/g, '<br>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #4ecdc4;">$1</a>')
  return html || '<p style="color: #909399;">暂无更新说明</p>'
}

const checkUpdate = async (showModal = false) => {
  console.log('[更新检查] 开始检查更新, showModal:', showModal)
  try {
    const response = await updateAPI.check()
    console.log('[更新检查] API响应:', response.data)
    if (response.data.has_update) {
      updateBadge.value = true
      console.log('[更新检查] 发现新版本:', response.data.latest_version, '当前版本:', response.data.current_version)
      if (showModal) {
        // 显示更新弹窗 - 调用后端渲染页面的弹窗函数
        if (typeof window.showUpdateModal === 'function') {
          console.log('[更新检查] 调用后端渲染页面的弹窗函数')
          window.showUpdateModal(response.data)
        } else {
          // 如果后端弹窗函数不存在，使用 Element Plus 弹窗
          console.log('[更新检查] 后端弹窗函数不存在，使用 Element Plus Dialog')
          showUpdateDialog(response.data)
        }
      }
    } else {
      updateBadge.value = false
      console.log('[更新检查] 已是最新版本')
    }
  } catch (error) {
    console.error('[更新检查] 检查更新失败:', error)
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

/* 子菜单样式 */
:deep(.el-sub-menu__title) {
  color: var(--el-text-color-regular);
}

:deep(.el-sub-menu__title:hover) {
  background: var(--el-fill-color-light);
}

:deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: var(--el-color-primary);
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
</style>
