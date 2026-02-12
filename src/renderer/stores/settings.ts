/**
 * 设置 Store
 */

import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ThemeMode } from '@shared/types'

export const useSettingsStore = defineStore('settings', () => {
  // State
  const theme = ref<ThemeMode>('system')
  const loading = ref(false)

  // Actions
  async function loadSettings() {
    loading.value = true
    
    try {
      const result = await window.api.settings.getAll()
      
      if (result.success && result.data) {
        const settings = result.data
        if (settings.theme) {
          theme.value = settings.theme as ThemeMode
        }
      }
    } finally {
      loading.value = false
    }
  }

  async function setTheme(value: ThemeMode) {
    theme.value = value
    
    await window.api.settings.set({
      key: 'theme',
      value
    })
    
    // 应用主题
    applyTheme(value)
  }

  function applyTheme(mode: ThemeMode) {
    const html = document.documentElement
    
    if (mode === 'dark') {
      html.classList.add('dark')
      html.classList.remove('light')
    } else if (mode === 'light') {
      html.classList.add('light')
      html.classList.remove('dark')
    } else {
      // system
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        html.classList.add('dark')
        html.classList.remove('light')
      } else {
        html.classList.add('light')
        html.classList.remove('dark')
      }
    }
  }

  return {
    theme,
    loading,
    loadSettings,
    setTheme,
    applyTheme
  }
})
