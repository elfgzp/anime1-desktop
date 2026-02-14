/**
 * Vitest Configuration - Integration Tests
 * 
 * 运行: npm run test:integration
 * 或: npx vitest --config vitest.integration.config.js
 */
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    name: 'integration',  // 测试套件名称
    environment: 'node',  // 集成测试使用 node 环境
    globals: true,
    include: ['tests/integration/**/*.{test,spec}.{js,ts}'],
    exclude: ['node_modules', '.webpack', 'dist'],
    // 集成测试可能更耗时
    testTimeout: 30000,  // 30秒超时
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
