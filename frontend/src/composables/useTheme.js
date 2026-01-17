import { ref, onUnmounted } from 'vue'
import { settingsAPI } from '../utils/api'
import { THEME, RESPONSE_FIELDS, REQUEST_PARAMS } from '../constants/api'

// 使用单例模式避免重复创建
let currentTheme = ref(THEME.SYSTEM)
let isDark = ref(false)
let mediaQuery = null
let mediaListener = null

export function useThemeStore() {
  // 初始化媒体查询监听器
  const initMediaListener = () => {
    if (typeof window === 'undefined') return

    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaListener = (e) => {
      if (currentTheme.value === THEME.SYSTEM) {
        applyTheme(THEME.SYSTEM)
      }
    }
    mediaQuery.addEventListener('change', mediaListener)
  }

  // 清理媒体查询监听器
  const cleanupMediaListener = () => {
    if (mediaQuery && mediaListener) {
      mediaQuery.removeEventListener('change', mediaListener)
      mediaQuery = null
      mediaListener = null
    }
  }

  const initTheme = async () => {
    try {
      const response = await settingsAPI.getTheme()
      // Handle standardized response format: { success: true, data: { theme: "dark" } }
      if (response.data && response.data.success && response.data.data) {
        currentTheme.value = response.data.data.theme
        applyTheme(currentTheme.value)
      } else {
        // Fallback if response format is unexpected
        console.warn('Unexpected theme response format, using default')
        applyTheme(THEME.DARK)
      }
    } catch (error) {
      console.error('Error loading theme:', error)
      applyTheme(THEME.DARK) // Default to dark theme
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
    } catch (error) {
      console.error('Error saving theme:', error)
    }
  }

  // 组件卸载时清理监听器
  onUnmounted(() => {
    cleanupMediaListener()
  })

  return {
    currentTheme,
    isDark,
    initTheme,
    applyTheme,
    saveTheme
  }
}
