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

    <!-- 番剧网格 -->
    <div v-if="animeList.length > 0 || loading" class="anime-grid" v-loading="loading" element-loading-text="正在加载番剧..." element-loading-spinner="动漫loading">
      <el-card
        v-for="anime in animeList"
        :key="anime.id"
        class="anime-card"
        shadow="hover"
        :body-style="{ padding: '0' }"
      >
        <router-link :to="ROUTES.ANIME_DETAIL(anime.id)" class="card-link">
          <div class="card-cover" :class="{ 'cover-loading': coverLoadingMap[anime.id] }">
            <!-- 封面图片 -->
            <img
              v-if="anime.cover_url"
              :src="anime.cover_url"
              :alt="anime.title"
              class="cover-image"
              @load="handleImageLoad(anime.id)"
              @error="handleImageError(anime.id)"
            />
            <!-- 封面加载中骨架屏 -->
            <div v-else-if="coverLoadingMap[anime.id]" class="cover-skeleton"></div>
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
    <el-backtop :right="20" :bottom="20" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, markRaw, nextTick } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave as originalOnBeforeRouteLeave } from 'vue-router'
import { Search, Star, StarFilled, Picture } from '@element-plus/icons-vue'
import { animeAPI, favoriteAPI } from '../utils/api'
import { ROUTES, ADULT_CONTENT, ERROR_MESSAGES, UI_TEXT } from '../constants/api'
import { RESPONSE_FIELDS } from '../constants/api'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'
import { measure, measureApi } from '../utils/performance'
import { onCacheCleared } from '../utils/cacheEventBus'

const loading = ref(false)
const animeList = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const searchKeyword = ref('')
const isSearching = ref(false)
const isFavoriteMap = ref({})
const coverLoadingMap = ref({})  // 跟踪封面加载状态

// 保存/恢复分页位置和搜索状态
const SCROLL_POSITION_KEY = 'anime_home_scroll_position'
const SEARCH_STATE_KEY = 'anime_home_search_state'
const router = useRouter()
const route = useRoute()
const animeGridRef = ref(null)

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
  const timer = measure('Home_fetchAnimeList')

  try {
    let response
    const apiTimer = measureApi('getAnimeList')
    if (isSearching.value && searchKeyword.value) {
      response = await animeAPI.search(searchKeyword.value, page)
    } else {
      response = await animeAPI.getList(page)
    }
    apiTimer.success(response)

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

    // 初始化封面加载状态
    animeList.value.forEach(anime => {
      if (!anime.cover_url && !anime._coverFailed) {
        coverLoadingMap.value[anime.id] = true
      }
    })

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
            // 使用 nextTick 确保骨架屏有足够时间显示
            nextTick(() => {
              anime.cover_url = cover.cover_url
              anime.year = cover.year || anime.year
              anime.season = cover.season || anime.season
              anime.subtitle_group = cover.subtitle_group || anime.subtitle_group
              // 图片加载完成后由 @load 事件清除 loading 状态
            })
          }
        }).catch(() => {
          // 加载失败，清除 loading 状态并显示占位符
          nextTick(() => {
            coverLoadingMap.value[anime.id] = false
            anime._coverFailed = true
          })
        })
      })
    }
    // 不等待封面，直接返回列表

    // 批量检查收藏状态（这个可以等待）
    await checkFavoritesStatus()

    timer.end({ page, count: animeList.value.length })
  } catch (error) {
    timer.end({ error: error.message })
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
  // 更新 URL
  router.replace({ query: { ...route.query, q: keyword, page: 1 } })
  fetchAnimeList(1)
}

const handleClearSearch = () => {
  searchKeyword.value = ''
  isSearching.value = false
  currentPage.value = 1
  // 清除 URL 中的搜索参数
  const query = { ...route.query }
  delete query.q
  delete query.page
  router.replace({ query })
  fetchAnimeList(1)
}

const handlePageChange = (page) => {
  // 更新 URL query 参数
  router.replace({ query: { ...route.query, page } })
  fetchAnimeList(page)
}

const handleImageError = (animeId) => {
  coverLoadingMap.value[animeId] = false
  // 找到对应的 anime 并设置 _coverFailed
  const anime = animeList.value.find(a => a.id === animeId)
  if (anime) anime._coverFailed = true
}

const handleImageLoad = (animeId) => {
  coverLoadingMap.value[animeId] = false
}

// 保存滚动位置和搜索状态
const saveScrollPosition = () => {
  const position = {
    scrollY: window.scrollY
  }
  sessionStorage.setItem(SCROLL_POSITION_KEY, JSON.stringify(position))
}

// 保存搜索状态到 sessionStorage
const saveSearchState = () => {
  const state = {
    searchKeyword: searchKeyword.value,
    isSearching: isSearching.value,
    currentPage: currentPage.value
  }
  sessionStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(state))
}

// 从 sessionStorage 恢复搜索状态
const restoreSearchState = () => {
  const saved = sessionStorage.getItem(SEARCH_STATE_KEY)
  if (saved) {
    try {
      const state = JSON.parse(saved)
      return {
        searchKeyword: state.searchKeyword || '',
        isSearching: state.isSearching || false,
        currentPage: state.currentPage || 1
      }
    } catch (e) {
      console.error('恢复搜索状态失败:', e)
    }
  }
  return null
}

// 恢复滚动位置（搜索和分页从 URL 读取）
const restoreScrollPosition = () => {
  const saved = sessionStorage.getItem(SCROLL_POSITION_KEY)
  if (saved) {
    try {
      const position = JSON.parse(saved)
      return position
    } catch (e) {
      console.error('恢复滚动位置失败:', e)
    }
  }
  return null
}

// 路由守卫：离开前保存位置和搜索状态
originalOnBeforeRouteLeave((to, from, next) => {
  saveScrollPosition()
  saveSearchState()
  next()
})

onMounted(async () => {
  // 监听缓存清理事件，清理后重新加载封面数据
  const cleanupCacheListener = onCacheCleared(() => {
    console.log('[Home] 收到缓存清理事件，刷新封面数据...')
    // 重新获取所有番剧的封面数据
    animeList.value.forEach(anime => {
      anime.cover_url = null
      anime.year = null
      anime.season = null
      anime.subtitle_group = null
    })
    // 后台重新加载封面
    fetchAnimeList(currentPage.value)
  })

  // 从 URL query 读取状态（搜索和分页都从 URL 读取）
  const urlKeyword = route.query.q || ''

  // 恢复滚动位置（用于从其他页面返回时）
  const savedPosition = restoreScrollPosition()

  // URL 有搜索词就设置搜索状态，否则从 sessionStorage 恢复
  if (urlKeyword) {
    searchKeyword.value = urlKeyword
    isSearching.value = true
    // 保存搜索状态到 sessionStorage
    saveSearchState()
  } else {
    // 尝试从 sessionStorage 恢复搜索状态
    const savedState = restoreSearchState()
    if (savedState && savedState.isSearching) {
      searchKeyword.value = savedState.searchKeyword
      isSearching.value = true
      currentPage.value = savedState.currentPage
    } else {
      searchKeyword.value = ''
      isSearching.value = false
      currentPage.value = 1
    }
  }

  // 搜索模式下页码从1开始
  if (isSearching.value) {
    fetchAnimeList(1)
  } else {
    fetchAnimeList(currentPage.value)
  }

  // 数据加载完成后恢复滚动位置
  await nextTick()
  if (savedPosition?.scrollY > 0) {
    window.scrollTo({ top: savedPosition.scrollY, behavior: 'instant' })
  }
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

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.anime-card:hover .cover-image {
  transform: scale(1.05);
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

.cover-skeleton {
  width: 100%;
  height: 100%;
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
  background: rgba(124, 92, 255, 0.85);
  border: 2px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  z-index: 10;
  color: #fff;
  box-shadow: 0 2px 8px rgba(124, 92, 255, 0.4);
  transition: all 0.3s;
}

.favorite-btn:hover {
  background: rgba(124, 92, 255, 1);
  transform: scale(1.15);
  box-shadow: 0 4px 12px rgba(124, 92, 255, 0.6);
}

.favorite-btn.active {
  background: rgba(255, 107, 157, 0.95);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 2px 8px rgba(255, 107, 157, 0.5);
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
