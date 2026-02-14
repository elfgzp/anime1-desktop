/**
 * Vitest Configuration - Unit Tests Only
 * 
 * 运行: npm run test:unit
 * 或: npx vitest --config vitest.unit.config.js
 */
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    name: 'unit',  // 测试套件名称
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', '.webpack', 'dist'],
    // 允许未捕获的异常，不导致测试失败
    teardownTimeout: 5000,
    // 忽略某些测试文件中的未处理 rejection
    onConsoleLog(log) {
      if (log.includes('InvalidArgumentError')) return false
      return true
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        '.webpack/',
        'tests/',
        '**/*.config.js',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '~': path.resolve(__dirname, '.'),
    },
  },
})
