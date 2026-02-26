import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import { resolve } from 'path'
import { copyFileSync, mkdirSync, existsSync, rmSync } from 'fs'

// 复制 preload 文件插件 - 直接复制不编译
const copyPreloadPlugin = () => ({
  name: 'copy-preload',
  writeBundle() {
    const src = resolve(__dirname, 'src/preload/index.cjs')
    const dest = resolve(__dirname, 'dist-electron/preload/index.cjs')
    const wrongFile = resolve(__dirname, 'dist-electron/preload/index.js')
    
    try {
      // 确保目录存在
      if (!existsSync(resolve(__dirname, 'dist-electron/preload'))) {
        mkdirSync(resolve(__dirname, 'dist-electron/preload'), { recursive: true })
      }
      
      // 直接复制文件
      copyFileSync(src, dest)
      console.log('[copyPreload] Copied:', src, '->', dest)
      
      // 删除 vite 生成的错误文件（如果存在）
      if (existsSync(wrongFile)) {
        rmSync(wrongFile)
        console.log('[copyPreload] Removed wrong file:', wrongFile)
      }
    } catch (e: any) {
      console.error('[copyPreload] Error:', e.message)
    }
  }
})

export default defineConfig({
  optimizeDeps: {
    exclude: ['libsql', 'better-sqlite3']
  },
  plugins: [
    vue(),
    electron([
      {
        // Main process entry
        entry: resolve(__dirname, 'src/main/index.ts'),
        onstart({ startup }) {
          startup()
        },
        vite: {
          resolve: {
            alias: {
              '@': resolve(__dirname, 'src'),
              '@main': resolve(__dirname, 'src/main'),
              '@preload': resolve(__dirname, 'src/preload'),
              '@renderer': resolve(__dirname, 'src/renderer'),
              '@shared': resolve(__dirname, 'src/shared')
            }
          },
          build: {
            sourcemap: true,
            minify: process.env.NODE_ENV === 'production',
            outDir: resolve(__dirname, 'dist-electron/main'),
            rollupOptions: {
              external: ['better-sqlite3', 'libsql', /^libsql-.*/, 'node:sqlite', 'undici', 'electron-log']
            }
          }
        }
      },
      {
        // Preload script - 使用虚拟入口，实际通过插件复制
        entry: resolve(__dirname, 'src/main/index.ts'), // 虚拟入口，不会实际使用
        onstart({ reload }) {
          reload()
        },
        vite: {
          plugins: [copyPreloadPlugin()],
          build: {
            // 不实际构建 preload，只是触发 copy 插件
            outDir: resolve(__dirname, 'dist-electron/preload'),
            rollupOptions: {
              input: resolve(__dirname, 'src/preload/index.cjs')
            }
          }
        }
      }
    ]),
    renderer()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@main': resolve(__dirname, 'src/main'),
      '@preload': resolve(__dirname, 'src/preload'),
      '@renderer': resolve(__dirname, 'src/renderer'),
      '@shared': resolve(__dirname, 'src/shared')
    }
  },
  root: resolve(__dirname, 'src/renderer'),
  publicDir: resolve(__dirname, 'resources'),
  build: {
    outDir: resolve(__dirname, 'dist'),
    emptyOutDir: true,
    sourcemap: true
  },
  server: {
    port: 5173
  }
})
