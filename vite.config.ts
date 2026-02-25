import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import { resolve } from 'path'
import { readFileSync, writeFileSync, existsSync } from 'fs'

// 修复 preload 文件：将 ES Module 语法转换为 CommonJS
import { writeFileSync as writeFile, existsSync as exists, readFileSync as readFile } from 'fs'

function fixPreloadFile() {
  const preloadPath = resolve(__dirname, 'dist-electron/preload/index.cjs')
  const lockPath = resolve(__dirname, 'dist-electron/preload/.fixed')
  
  if (!exists(preloadPath)) {
    console.log('[fixPreload] File not found:', preloadPath)
    return
  }
  
  // 使用文件锁防止重复处理
  if (exists(lockPath)) {
    console.log('[fixPreload] Already fixed (lock file exists)')
    return
  }
  
  try {
    let content = readFile(preloadPath, 'utf8')
    
    // 检查是否已经修复过（避免重复追加）
    if (content.includes('module.exports = require_index()')) {
      console.log('[fixPreload] Already fixed (module.exports found)')
      // 创建锁文件
      writeFile(lockPath, 'fixed', 'utf8')
      return
    }
    
    // 检查是否需要修复
    if (!content.includes('export default require_index()')) {
      console.log('[fixPreload] No fix needed (already CommonJS or different format)')
      // 创建锁文件
      writeFile(lockPath, 'fixed', 'utf8')
      return
    }
    
    // 替换 export default 为 module.exports
    content = content.replace(/export\s+default\s+require_index\(\);/, 'module.exports = require_index();')
    writeFile(preloadPath, content, 'utf8')
    // 创建锁文件
    writeFile(lockPath, 'fixed', 'utf8')
    console.log('[fixPreload] Fixed preload file:', preloadPath)
  } catch (e: any) {
    console.error('[fixPreload] Error:', e.message)
  }
}

// Vite 插件：在构建完成后修复 preload 文件
const fixPreloadPlugin = () => ({
  name: 'fix-preload',
  writeBundle(options: any) {
    if (options.dir?.includes('preload') || options.fileName?.includes('preload')) {
      fixPreloadFile()
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
        // Preload script entry
        entry: resolve(__dirname, 'src/preload/index.ts'),
        onstart({ reload }) {
          reload()
        },
        vite: {
          plugins: [fixPreloadPlugin()],
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
            minify: false,
            outDir: resolve(__dirname, 'dist-electron/preload'),
            lib: {
              entry: resolve(__dirname, 'src/preload/index.ts'),
              formats: ['cjs'],
              fileName: () => 'index.cjs'
            },
            rollupOptions: {
              external: ['electron']
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
