/**
 * Vue Router 配置
 */

import { createRouter, createWebHashHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Home from '../views/Home.vue'

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
        path: 'anime/:id',
        name: 'Detail',
        component: () => import('../views/Detail.vue')
      },
      {
        path: 'favorites',
        name: 'Favorites',
        component: () => import('../views/Favorites.vue')
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('../views/History.vue')
      },
      {
        path: 'downloads',
        name: 'Downloads',
        component: () => import('../views/Downloads.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
