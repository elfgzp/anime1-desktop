import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Get Flask port from environment variable (set by dev.py)
const flaskPort = process.env.FLASK_PORT || 5172

export default defineConfig({
  plugins: [vue()],
  root: 'frontend',
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    // Generate manifest for asset mapping
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/index.html')
      },
      output: {
        // Use consistent naming for easier template reference
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  },
  server: {
    port: 5173,
    host: true,
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
  // Enable HMR with Vue plugin
  esbuild: {
    // Disable minification in dev mode for faster rebuild
    minify: false
  }
})
