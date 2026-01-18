import { ref } from 'vue'
import { settingsAPI } from '../utils/api'
import { THEME, RESPONSE_FIELDS, REQUEST_PARAMS } from '../constants/api'

// 使用单例模式避免重复创建
let currentTheme = ref(THEME.SYSTEM)
let isDark = ref(false)
let mediaQuery = null
let mediaListener = null
let mediaListenerInitialized = false  // 标记是否已初始化监听器
const THEME_STORAGE_KEY = 'anime1_theme'

export function useThemeStore() {
  // 从 localStorage 读取主题（同步，立即应用）
  const loadThemeFromStorage = () => {
    if (typeof window === 'undefined') return THEME.SYSTEM
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY)
      if (saved && Object.values(THEME).includes(saved)) {
        return saved
      }
    } catch (e) {
      console.warn('Failed to load theme from localStorage:', e)
    }
    return THEME.SYSTEM
  }

  // 初始化媒体查询监听器（只初始化一次）
  const initMediaListener = () => {
    if (typeof window === 'undefined' || mediaListenerInitialized) return
    if (mediaQuery && mediaListener) return  // 已有监听器，直接返回

    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaListener = (e) => {
      if (currentTheme.value === THEME.SYSTEM) {
        applyTheme(THEME.SYSTEM)
      }
    }
    mediaQuery.addEventListener('change', mediaListener)
    mediaListenerInitialized = true
  }

  // 清理媒体查询监听器（仅在页面真正卸载时调用）
  const cleanupMediaListener = () => {
    // 注意：这个函数不再通过 onUnmounted 自动调用
    // 媒体查询监听器是全局的，保持到页面真正卸载
  }

  const initTheme = async () => {
    // 优先从 localStorage 读取并立即应用，避免闪烁
    const storageTheme = loadThemeFromStorage()
    applyTheme(storageTheme)

    try {
      const response = await settingsAPI.getTheme()
      // Handle standardized response format: { success: true, data: { theme: "dark" } }
      if (response.data && response.data.success && response.data.data) {
        const serverTheme = response.data.data.theme
        currentTheme.value = serverTheme
        applyTheme(serverTheme)
        // 同步到 localStorage
        try {
          localStorage.setItem(THEME_STORAGE_KEY, serverTheme)
        } catch (e) {
          console.warn('Failed to save theme to localStorage:', e)
        }
      } else {
        // Fallback if response format is unexpected, keep localStorage theme
        console.warn('Unexpected theme response format, using localStorage theme')
      }
    } catch (error) {
      console.error('Error loading theme:', error)
      // Keep localStorage theme as fallback
    }

    // Initialize media query listener
    initMediaListener()
  }

  const applyTheme = (theme) => {
    currentTheme.value = theme
    const html = document.documentElement

    if (theme === THEME.SYSTEM) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = prefersDark
      html.classList.remove('dark', 'light')
      html.classList.add(prefersDark ? 'dark' : 'light')
    } else {
      isDark.value = theme === THEME.DARK
      html.classList.remove('dark', 'light')
      html.classList.add(theme)
    }

    // Element Plus 暗色主题
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  const saveTheme = async (theme) => {
    try {
      await settingsAPI.saveTheme(theme)
      applyTheme(theme)
      // 同步到 localStorage
      try {
        localStorage.setItem(THEME_STORAGE_KEY, theme)
      } catch (e) {
        console.warn('Failed to save theme to localStorage:', e)
      }
    } catch (error) {
      console.error('Error saving theme:', error)
    }
  }

  return {
    currentTheme,
    isDark,
    initTheme,
    applyTheme,
    saveTheme
  }
}
