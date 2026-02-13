import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './composables/useTheme'

// Wait for electronAPI to be available
const waitForElectronAPI = () => {
  return new Promise((resolve) => {
    if (window.electronAPI) {
      resolve()
      return
    }
    
    // Check every 50ms for up to 5 seconds
    let attempts = 0
    const maxAttempts = 100
    
    const check = () => {
      attempts++
      if (window.electronAPI) {
        console.log('[Renderer] electronAPI available after', attempts, 'attempts')
        resolve()
      } else if (attempts >= maxAttempts) {
        console.error('[Renderer] electronAPI not available after', maxAttempts, 'attempts')
        resolve() // Resolve anyway to show error in UI
      } else {
        setTimeout(check, 50)
      }
    }
    
    check()
  })
}

// Initialize app after electronAPI is ready
const initApp = async () => {
  console.log('[Renderer] Waiting for electronAPI...')
  await waitForElectronAPI()
  console.log('[Renderer] electronAPI ready, mounting app...')
  
  const app = createApp(App)

  // 注册所有图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  app.use(ElementPlus, {
    locale: zhCn,
  })

  app.use(router)

  // 初始化主题
  const themeStore = useThemeStore()
  themeStore.initTheme()

  // 监听系统主题变化
  if (typeof window !== 'undefined') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', () => {
      if (themeStore.currentTheme.value === 'system') {
        themeStore.applyTheme('system')
      }
    })
  }

  app.mount('#app')
  console.log('[Renderer] App mounted successfully')
}

initApp()
