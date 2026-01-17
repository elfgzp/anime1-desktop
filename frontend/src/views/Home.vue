<template>
  <div class="home-container">
    <!-- 搜索框 -->
    <el-card class="search-card" shadow="never">
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索番剧名称..."
          clearable
          @keyup.enter="handleSearch"
          @clear="handleClearSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch" :icon="Search">搜索</el-button>
        <el-button v-if="isSearching" @click="handleClearSearch">清除搜索</el-button>
      </div>
    </el-card>

    <!-- 加载中 -->
    <el-skeleton v-if="loading" :rows="10" animated />

    <!-- 番剧网格 -->
    <div v-else-if="animeList.length > 0" class="anime-grid">
      <el-card
        v-for="anime in animeList"
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
              :hide-on-click="true"
              @error="handleImageError(anime)"
            />
            <div v-else-if="isAdult(anime)" class="adult-mark">🔞</div>
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
          :icon="isFavoriteMap[anime.id] ? StarFilled : Star"
          circle
          class="favorite-btn"
          :class="{ active: isFavoriteMap[anime.id] }"
          @click.stop="toggleFavorite(anime.id)"
        />
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else :description="UI_TEXT.NO_DATA" />

    <!-- 分页 -->
    <el-pagination
      v-if="totalPages > 1"
      v-model:current-page="currentPage"
      :page-size="20"
      :total="totalPages * 20"
      layout="prev, pager, next, jumper"
      @current-change="handlePageChange"
      class="pagination"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, markRaw } from 'vue'
import { Search, Star, StarFilled, Picture } from '@element-plus/icons-vue'
import { animeAPI, favoriteAPI } from '../utils/api'
import { ROUTES, ADULT_CONTENT, ERROR_MESSAGES, UI_TEXT } from '../constants/api'
import { RESPONSE_FIELDS } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const animeList = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const searchKeyword = ref('')
const isSearching = ref(false)
const isFavoriteMap = ref({})

// 安全转义文本 - 防止 XSS
const escapeText = (text) => {
  if (text == null) return ''
  return DOMPurify.sanitize(String(text), { ALLOWED_TAGS: [], KEEP_CONTENT: true })
}

// 安全获取属性值
const getAnimeAttr = (anime, attr, defaultValue = '') => {
  const value = anime[attr]
  return escapeText(value || defaultValue)
}

// 成人内容检测（使用转义后的值进行比较）
const isAdult = (anime) => {
  const title = escapeText(anime.title)
  const detailUrl = escapeText(anime.detail_url)
  return title.includes(ADULT_CONTENT.MARKER) ||
         detailUrl.includes(ADULT_CONTENT.DOMAIN)
}

const fetchAnimeList = async (page = 1) => {
  loading.value = true
  try {
    let response
    if (isSearching.value && searchKeyword.value) {
      response = await animeAPI.search(searchKeyword.value, page)
    } else {
      response = await animeAPI.getList(page)
    }

    const data = response.data
    const rawList = data.anime_list || []

    // 净化数据防止 XSS
    animeList.value = rawList.map(anime => ({
      ...anime,
      title: escapeText(anime.title),
      year: escapeText(anime.year),
      season: escapeText(anime.season),
      subtitle_group: escapeText(anime.subtitle_group),
      detail_url: escapeText(anime.detail_url)
    }))

    currentPage.value = data.current_page || page
    totalPages.value = data.total_pages || 1
    
    // 异步获取封面和详情（先显示列表，后台加载数据）
    if (animeList.value.length > 0) {
      const normalAnime = animeList.value.filter(anime => !isAdult(anime))
      // 立即显示列表，不需要等待封面
      normalAnime.forEach(anime => {
        // 启动后台加载封面
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
    // 不等待封面，直接返回列表

    // 批量检查收藏状态（这个可以等待）
    await checkFavoritesStatus()
    } catch (error) {
      console.error('获取番剧列表失败:', error)
      ElMessage.error(ERROR_MESSAGES.NETWORK_ERROR)
    } finally {
    loading.value = false
  }
}

const checkFavoritesStatus = async () => {
  if (animeList.value.length === 0) return

  // 使用批量接口一次性获取所有收藏状态
  const ids = animeList.value.map(a => a.id).join(',')
  try {
    const response = await favoriteAPI.batchStatus(ids)
    if (response.data.data) {
      isFavoriteMap.value = response.data.data
    }
  } catch (error) {
    console.error('批量检查收藏状态失败:', error)
    // 降级到单独检查（不显示错误提示，因为不影响主要功能）
    const promises = animeList.value.map(async (anime) => {
      try {
        const response = await favoriteAPI.isFavorite(anime.id)
        isFavoriteMap.value[anime.id] = response.data.data?.is_favorite || false
      } catch {
        isFavoriteMap.value[anime.id] = false
      }
    })
    await Promise.all(promises)
  }
}

const toggleFavorite = async (animeId) => {
  const isFavorite = isFavoriteMap.value[animeId]
  try {
    if (isFavorite) {
      await favoriteAPI.remove(animeId)
      ElMessage.success(UI_TEXT.FAVORITE_REMOVED)
    } else {
      await favoriteAPI.add(animeId)
      ElMessage.success(UI_TEXT.FAVORITE_ADDED)
    }
    isFavoriteMap.value[animeId] = !isFavorite
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    // 使用拦截器中的 userMessage
    const message = error.userMessage || ERROR_MESSAGES.OPERATION_FAILED
    ElMessage.error(message)
  }
}

const handleSearch = () => {
  const keyword = searchKeyword.value?.trim() || ''
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  isSearching.value = true
  currentPage.value = 1
  fetchAnimeList(1)
}

const handleClearSearch = () => {
  searchKeyword.value = ''
  isSearching.value = false
  currentPage.value = 1
  fetchAnimeList(1)
}

const handlePageChange = (page) => {
  fetchAnimeList(page)
}

const handleImageError = (anime) => {
  anime._coverFailed = true
}

onMounted(() => {
  fetchAnimeList(1)
})
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}

.search-box {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
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

.adult-mark,
.no-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: linear-gradient(135deg, #252542 0%, #1a1a2e 100%);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  color: var(--el-text-color-placeholder);
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color) 100%);
}

.cover-loading {
  background: linear-gradient(90deg,
    var(--el-fill-color-light) 25%,
    var(--el-fill-color) 50%,
    var(--el-fill-color-light) 75%
  );
  background-size: 200% 100%;
  animation: cover-loading 1.5s infinite;
}

@keyframes cover-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.adult-mark {
  color: #ff6b6b;
}

.no-cover {
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
  background: rgba(0, 0, 0, 0.6);
  border: none;
  backdrop-filter: blur(4px);
  z-index: 10;
}

.favorite-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: scale(1.1);
}

.favorite-btn.active {
  background: rgba(255, 107, 157, 0.8);
  color: #fff;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .search-box {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
}
</style>
