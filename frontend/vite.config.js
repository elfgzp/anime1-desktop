import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 从环境变量读取 Flask 端口，默认 5172
const flaskPort = process.env.FLASK_PORT || 5172

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    hmr: true,  // 启用热更新
    proxy: {
      '/api': {
        target: `http://localhost:${flaskPort}`,
        changeOrigin: true
      },
      '/proxy': {
        target: `http://localhost:${flaskPort}`,
        changeOrigin: true
      }
    }
  },
  build: {
    // 生成 manifest.json 用于资源注入
    manifest: true,
    // 禁用构建缓存
    cache: false,
    rollupOptions: {
      output: {
        // 使用 hash 确保文件名唯一，避免缓存
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  },
  // 开发模式禁用缓存
  cacheDir: false
})
