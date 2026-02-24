<template>
  <div class="favorites-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1>我的追番</h1>
      <div class="header-actions">
        <el-button :icon="Refresh" circle @click="refreshFavorites" :loading="loading" />
      </div>
    </header>

    <main class="main-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <el-empty
        v-else-if="favorites.length === 0"
        description="还没有收藏任何番剧"
      >
        <template #image>
          <el-icon :size="80" color="#dcdfe6"><Star /></el-icon>
        </template>
        <el-button type="primary" @click="goToHome">去浏览番剧</el-button>
      </el-empty>

      <!-- 收藏列表 -->
      <div v-else class="favorites-grid">
        <el-card
          v-for="item in favorites"
          :key="item.animeId"
          class="anime-card"
          shadow="hover"
        >
          <div class="card-content" @click="goToDetail(item.animeId)">
            <div class="cover-wrapper">
              <el-image
                :src="item.coverUrl || defaultCover"
                fit="cover"
                loading="lazy"
              >
                <template #error>
                  <div class="cover-placeholder">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
            <div class="info-wrapper">
              <h3 class="anime-title" :title="item.title">{{ item.title }}</h3>
              <p class="anime-date">收藏于 {{ formatDate(item.createdAt) }}</p>
            </div>
          </div>
          
          <div class="card-actions">
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click.stop="removeFavorite(item)"
            >
              取消收藏
            </el-button>
          </div>
        </el-card>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Star, Refresh, Picture, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

interface FavoriteAnime {
  animeId: string
  title: string
  coverUrl?: string
  detailUrl: string
  createdAt: number
}

const router = useRouter()

const favorites = ref<FavoriteAnime[]>([])
const loading = ref(false)

const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="300"%3E%3Crect fill="%23f0f0f0" width="200" height="300"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="14" dy=".3em" text-anchor="middle" x="100" y="150"%3E暂无封面%3C/text%3E%3C/svg%3E'

// 格式化日期
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 加载收藏列表
const loadFavorites = async () => {
  loading.value = true
  try {
    const result = await window.api.favorite.getList()
    if (result.success) {
      favorites.value = result.data || []
    }
  } catch (err: any) {
    ElMessage.error(err.message || '加载收藏失败')
  } finally {
    loading.value = false
  }
}

// 刷新收藏
const refreshFavorites = () => {
  loadFavorites()
}

// 跳转到详情页
const goToDetail = (animeId: string) => {
  router.push(`/anime/${animeId}`)
}

// 跳转到首页
const goToHome = () => {
  router.push('/')
}

// 取消收藏
const removeFavorite = async (item: FavoriteAnime) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消收藏 "${item.title}" 吗？`,
      '确认取消收藏',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await window.api.favorite.remove({ animeId: item.animeId })
    if (result.success) {
      ElMessage.success('已取消收藏')
      // 从列表中移除
      favorites.value = favorites.value.filter(f => f.animeId !== item.animeId)
    }
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '操作失败')
    }
  }
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
  min-height: 100%;
  background: var(--el-bg-color-page);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.main-content {
  padding: 24px 40px;
}

.loading-state {
  padding: 40px;
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.anime-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-content {
  cursor: pointer;
}

.cover-wrapper {
  aspect-ratio: 2/3;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}

.cover-wrapper :deep(.el-image) {
  width: 100%;
  height: 100%;
}

.cover-wrapper :deep(.el-image__inner) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  color: var(--el-text-color-secondary);
  font-size: 32px;
}

.info-wrapper {
  padding: 0 4px;
}

.anime-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 40px;
}

.anime-date {
  margin: 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.card-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color);
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .main-content {
    padding: 16px 20px;
  }
  
  .favorites-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}
</style>
