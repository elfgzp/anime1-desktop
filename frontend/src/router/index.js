import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Home from '../views/Home.vue'
import Favorites from '../views/Favorites.vue'
import Settings from '../views/Settings.vue'
import Detail from '../views/Detail.vue'
import PlaybackHistory from '../views/PlaybackHistory.vue'

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
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
