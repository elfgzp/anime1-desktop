import axios from 'axios'
import {
  API_BASE,
  API_ENDPOINTS,
  REQUEST_PARAMS,
  RESPONSE_FIELDS,
  ERROR_MESSAGES
} from '../constants/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    // 如果后端返回了业务错误 (success: false)
    if (response.data && response.data.success === false) {
      const errorMessage = response.data.error || ERROR_MESSAGES.OPERATION_FAILED
      const error = new Error(errorMessage)
      error.isBusinessError = true
      error.responseData = response.data
      return Promise.reject(error)
    }
    return response
  },
  (error) => {
    // 网络错误处理
    if (!error.response) {
      error.userMessage = ERROR_MESSAGES.NETWORK_ERROR
      return Promise.reject(error)
    }

    // HTTP 错误状态码处理
    const status = error.response.status
    switch (status) {
      case 400:
        error.userMessage = error.response.data?.error || '请求参数错误'
        break
      case 401:
        error.userMessage = '未授权访问'
        break
      case 403:
        error.userMessage = '禁止访问'
        break
      case 404:
        error.userMessage = '资源不存在'
        break
      case 500:
        error.userMessage = '服务器错误，请稍后重试'
        break
      default:
        error.userMessage = ERROR_MESSAGES.UNKNOWN_ERROR
    }
    return Promise.reject(error)
  }
)

// 番剧相关 API
export const animeAPI = {
  // 获取番剧列表
  getList: (page = 1) => api.get(API_ENDPOINTS.ANIME.LIST, {
    params: { [REQUEST_PARAMS.PAGE]: page }
  }),

  // 搜索番剧
  search: (keyword, page = 1) => api.get(API_ENDPOINTS.ANIME.SEARCH, {
    params: {
      [REQUEST_PARAMS.KEYWORD]: keyword,
      [REQUEST_PARAMS.PAGE]: page
    }
  }),

  // 获取封面（只支持单个ID，不支持批量）
  getCover: (id) => api.get(API_ENDPOINTS.ANIME.COVERS, {
    params: { id }
  }),

  // 获取番剧详情和集数
  getEpisodes: (id) => api.get(API_ENDPOINTS.ANIME.EPISODES(id)),

  // 获取 Bangumi 番剧信息
  getBangumiInfo: (id) => api.get(API_ENDPOINTS.ANIME.BANGUMI(id)),

  // 通过前端获取的 HTML 内容获取 anime1.pw 番剧集数
  fetchPwEpisodes: (htmlContent, animeId) => api.post('/anime/pw/episodes', {
    html: htmlContent,
    anime_id: animeId
  })
}

// 收藏相关 API
export const favoriteAPI = {
  // 添加收藏
  add: (animeId) => api.post(API_ENDPOINTS.FAVORITE.ADD, {
    [REQUEST_PARAMS.ANIME_ID]: animeId
  }),
  
  // 移除收藏
  remove: (animeId) => api.post(API_ENDPOINTS.FAVORITE.REMOVE, {
    [REQUEST_PARAMS.ANIME_ID]: animeId
  }),
  
  // 获取收藏列表
  getList: () => api.get(API_ENDPOINTS.FAVORITE.LIST),
  
  // 检查收藏状态
  isFavorite: (animeId) => api.get(API_ENDPOINTS.FAVORITE.IS_FAVORITE, {
    params: { [REQUEST_PARAMS.ANIME_ID]: animeId }
  }),

  // 批量检查收藏状态
  batchStatus: (ids) => api.get(API_ENDPOINTS.FAVORITE.BATCH_STATUS, {
    params: { [REQUEST_PARAMS.IDS]: ids }
  }),

  // 检查更新
  checkUpdates: () => api.get(API_ENDPOINTS.FAVORITE.CHECK)
}

// 设置相关 API
export const settingsAPI = {
  // 获取主题
  getTheme: () => api.get(API_ENDPOINTS.SETTINGS.THEME),

  // 保存主题
  saveTheme: (theme) => api.post(API_ENDPOINTS.SETTINGS.THEME, {
    [REQUEST_PARAMS.THEME]: theme
  }),

  // 获取关于信息
  getAbout: () => api.get(API_ENDPOINTS.SETTINGS.ABOUT),

  // 检查更新
  checkUpdate: () => api.get(API_ENDPOINTS.SETTINGS.CHECK_UPDATE),

  // 打开日志文件夹
  openLogsFolder: () => api.post(API_ENDPOINTS.SETTINGS.LOGS_OPEN)
}

// 更新相关 API
export const updateAPI = {
  // 检查更新
  check: () => api.get(API_ENDPOINTS.UPDATE.CHECK),

  // 获取更新信息
  getInfo: () => api.get(API_ENDPOINTS.UPDATE.INFO)
}

// 播放历史相关 API
export const playbackAPI = {
  // 更新播放进度
  update: (data) => api.post(API_ENDPOINTS.PLAYBACK.UPDATE, data),

  // 获取播放历史列表
  getList: (limit = 50) => api.get(API_ENDPOINTS.PLAYBACK.LIST, {
    params: { limit }
  }),

  // 获取单集播放进度
  getEpisodeProgress: (animeId, episodeId) => api.get(API_ENDPOINTS.PLAYBACK.EPISODE, {
    params: {
      [REQUEST_PARAMS.ANIME_ID]: animeId,
      episode_id: episodeId
    }
  }),

  // 获取动漫最新播放进度
  getLatest: (animeId) => api.get(API_ENDPOINTS.PLAYBACK.LATEST, {
    params: { [REQUEST_PARAMS.ANIME_ID]: animeId }
  }),

  // 批量获取集数进度
  batchProgress: (ids) => api.get(API_ENDPOINTS.PLAYBACK.BATCH, {
    params: { [REQUEST_PARAMS.IDS]: ids }
  })
}

export default api
