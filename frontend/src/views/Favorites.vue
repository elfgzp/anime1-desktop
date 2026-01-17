<template>
  <div class="favorites-container">
    <el-card shadow="never" class="page-header-card">
      <h1 class="page-title">我的追番</h1>
    </el-card>

    <!-- 加载中 -->
    <el-skeleton v-if="loading" :rows="10" animated />

    <!-- 追番列表 -->
    <div v-else-if="favoritesList.length > 0" class="anime-grid">
      <el-card
        v-for="anime in favoritesList"
        :key="anime.id"
        class="anime-card"
        shadow="hover"
        :body-style="{ padding: '0' }"
      >
        <router-link :to="ROUTES.ANIME_DETAIL(anime.id)" class="card-link">
          <div class="card-cover" :class="{ 'cover-loading': !anime.cover_url && !anime._coverFailed }">
            <el-image
              v-if="anime.cover_url"
              :src="anime.cover_url"
              :alt="anime.title"
              fit="cover"
              loading="lazy"
              :preview-src-list="[]"
              @error="handleImageError(anime)"
            />
            <div v-else-if="anime._coverFailed" class="no-cover">📺</div>
            <div v-else class="cover-placeholder">
              <el-icon><Picture /></el-icon>
            </div>
          </div>
          <div class="card-content">
            <div class="card-title">{{ anime.title }}</div>
            <div class="card-meta">
              <el-tag size="small" type="info">第{{ anime.episode }}集</el-tag>
              <el-tag v-if="anime.year" size="small" type="danger">{{ anime.year }}</el-tag>
              <el-tag v-if="anime.season" size="small" type="success">{{ anime.season }}</el-tag>
              <el-tag v-if="anime.subtitle_group" size="small" type="warning">
                {{ anime.subtitle_group }}
              </el-tag>
            </div>
          </div>
        </router-link>
        <el-button
          :icon="StarFilled"
          circle
          class="favorite-btn active"
          @click.stop="removeFavorite(anime.id)"
        />
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else :description="UI_TEXT.NO_FAVORITES" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { StarFilled, Picture } from '@element-plus/icons-vue'
import { favoriteAPI, animeAPI } from '../utils/api'
import { ROUTES, ERROR_MESSAGES, UI_TEXT } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const favoritesList = ref([])

// 安全转义文本 - 防止 XSS
const escapeText = (text) => {
  if (text == null) return ''
  return DOMPurify.sanitize(String(text), { ALLOWED_TAGS: [], KEEP_CONTENT: true })
}

// 净化番剧数据
const sanitizeAnimeList = (list) => {
  return list.map(anime => ({
    ...anime,
    title: escapeText(anime.title),
    year: escapeText(anime.year),
    season: escapeText(anime.season),
    subtitle_group: escapeText(anime.subtitle_group)
  }))
}

const fetchFavorites = async () => {
  loading.value = true
  try {
    const response = await favoriteAPI.getList()
    if (response.data.success && response.data.data) {
      // 净化数据防止 XSS
      favoritesList.value = sanitizeAnimeList(response.data.data)

      // 异步获取封面（后台加载，不阻塞显示）
      if (favoritesList.value.length > 0) {
        favoritesList.value.forEach(anime => {
          animeAPI.getCover(anime.id).then(response => {
            if (response.data && response.data.length > 0) {
              const cover = response.data[0]
              if (cover.cover_url) anime.cover_url = cover.cover_url
              anime.year = cover.year || anime.year
              anime.season = cover.season || anime.season
              anime.subtitle_group = cover.subtitle_group || anime.subtitle_group
            }
          }).catch(() => {}) // 静默处理
        })
      }
    }
  } catch (error) {
    console.error('获取追番列表失败:', error)
    ElMessage.error(ERROR_MESSAGES.NETWORK_ERROR)
  } finally {
    loading.value = false
  }
}

const removeFavorite = async (animeId) => {
  try {
    await favoriteAPI.remove(animeId)
    ElMessage.success(UI_TEXT.FAVORITE_REMOVED)
    favoritesList.value = favoritesList.value.filter(a => a.id !== animeId)
  } catch (error) {
    console.error('取消追番失败:', error)
    ElMessage.error(ERROR_MESSAGES.OPERATION_FAILED)
  }
}

const handleImageError = (anime) => {
  anime._coverFailed = true
}

onMounted(() => {
  fetchFavorites()
})
</script>

<style scoped>
.favorites-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header-card {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.anime-card {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  transition: transform 0.3s, box-shadow 0.3s, border-color 0.3s;
  border: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.anime-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(124, 92, 255, 0.2);
  border-color: var(--el-color-primary);
}

.card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.card-cover {
  width: 100%;
  aspect-ratio: 2/3;
  overflow: hidden;
  position: relative;
  background: var(--el-fill-color-light);
}

.card-cover :deep(.el-image) {
  width: 100%;
  height: 100%;
  transition: transform 0.3s;
}

.anime-card:hover .card-cover :deep(.el-image) {
  transform: scale(1.05);
}

.no-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: linear-gradient(135deg, #252542 0%, #1a1a2e 100%);
  color: var(--el-text-color-placeholder);
}

.card-content {
  padding: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.favorite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: rgba(255, 107, 157, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  z-index: 10;
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 107, 157, 0.4);
  transition: all 0.3s;
}

.favorite-btn:hover {
  background: rgba(255, 107, 157, 1);
  transform: scale(1.15);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.6);
}

@media (max-width: 768px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }
}
</style>
