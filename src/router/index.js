import { createRouter, createWebHashHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Home from '../views/Home.vue'
import Favorites from '../views/Favorites.vue'
import Settings from '../views/Settings.vue'
import Detail from '../views/Detail.vue'
import PlaybackHistory from '../views/PlaybackHistory.vue'
import Performance from '../views/Performance.vue'
import Logs from '../views/Logs.vue'
import AutoDownload from '../views/AutoDownload.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Home',
        component: Home
      },
      {
        path: 'favorites',
        name: 'Favorites',
        component: Favorites
      },
      {
        path: 'playback',
        name: 'PlaybackHistory',
        component: PlaybackHistory
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings
      },
      {
        path: 'anime/:id',
        name: 'Detail',
        component: Detail
      },
      {
        path: 'dev/performance',
        name: 'Performance',
        component: Performance,
        meta: { devOnly: true }
      },
      {
        path: 'dev/logs',
        name: 'Logs',
        component: Logs,
        meta: { devOnly: true }
      },
      {
        path: 'auto-download',
        name: 'AutoDownload',
        component: AutoDownload
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 开发模式路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.devOnly) {
    const isDev = import.meta.env.DEV || window.location.port === '5173'
    if (!isDev) {
      // 非开发模式，重定向到首页
      next({ path: '/' })
      return
    }
  }
  next()
})

export default router
