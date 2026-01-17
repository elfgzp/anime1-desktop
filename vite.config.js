import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Get Flask port from environment variable (set by dev.py)
const flaskPort = process.env.FLASK_PORT || 5172

// Resolve paths from the project root
const pathResolve = (dir) => resolve(__dirname, dir)

export default defineConfig({
  plugins: [vue()],
  // Use absolute paths relative to this config file location
  root: pathResolve('frontend'),
  build: {
    outDir: pathResolve('static/dist'),
    emptyOutDir: true,
    // Generate manifest for asset mapping
    manifest: true,
    rollupOptions: {
      input: {
        main: pathResolve('frontend/index.html')
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
