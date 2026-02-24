import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import electron from 'vite-plugin-electron'
import renderer from 'vite-plugin-electron-renderer'
import { resolve } from 'path'

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
              external: ['better-sqlite3', 'libsql', /^libsql-.*/, 'node:sqlite', 'undici']
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
