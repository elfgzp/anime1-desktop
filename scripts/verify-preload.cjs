#!/usr/bin/env node
/**
 * 验证 preload 文件是否正确
 * 在应用启动前运行，确保 window.api 可用
 * 
 * ⚠️ 重要: 此脚本会检查是否存在重复的 TypeScript preload 文件
 * 唯一真相源是 src/preload/index.cjs，不要创建 index.ts！
 */

const fs = require('fs')
const path = require('path')

const PRELOAD_SRC = path.resolve(__dirname, '../src/preload/index.cjs')
const PRELOAD_DEST = path.resolve(__dirname, '../dist-electron/preload/index.cjs')
const PRELOAD_TS = path.resolve(__dirname, '../src/preload/index.ts')

function verifyPreload() {
  console.log('[verify-preload] Checking preload files...')
  
  // ⚠️ 检查是否存在错误的 TypeScript 文件
  if (fs.existsSync(PRELOAD_TS)) {
    console.error('\n[verify-preload] ⚠️⚠️⚠️ 严重警告 ⚠️⚠️⚠️')
    console.error('[verify-preload] 发现 src/preload/index.ts 文件！')
    console.error('[verify-preload] 唯一真相源是 src/preload/index.cjs')
    console.error('[verify-preload] 请不要创建 .ts 文件，所有修改请在 .cjs 文件中进行')
    console.error('[verify-preload] 如需类型定义，请在 src/shared/types/api.ts 中添加\n')
    process.exit(1)
  }
  
  // 检查源文件
  if (!fs.existsSync(PRELOAD_SRC)) {
    console.error('[verify-preload] ERROR: Source file not found:', PRELOAD_SRC)
    process.exit(1)
  }
  
  const srcContent = fs.readFileSync(PRELOAD_SRC, 'utf8')
  
  // 验证源文件格式
  if (srcContent.includes('export ') && !srcContent.includes('module.exports')) {
    console.error('[verify-preload] ERROR: Source file contains ES Module syntax!')
    console.error('[verify-preload] Please use CommonJS syntax (require/module.exports)')
    process.exit(1)
  }
  
  // 确保目标目录存在
  const destDir = path.dirname(PRELOAD_DEST)
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true })
    console.log('[verify-preload] Created directory:', destDir)
  }
  
  // 复制文件到目标位置
  fs.copyFileSync(PRELOAD_SRC, PRELOAD_DEST)
  console.log('[verify-preload] Copied:', PRELOAD_SRC, '->', PRELOAD_DEST)
  
  // 验证目标文件
  const destContent = fs.readFileSync(PRELOAD_DEST, 'utf8')
  
  // 检查关键内容
  const checks = [
    { pattern: /require\(['"]electron['"]\)/, desc: ' electron import' },
    { pattern: /contextBridge\.exposeInMainWorld/, desc: ' API exposure' },
    { pattern: /module\.exports|exports\./, desc: ' CommonJS export (optional)' }
  ]
  
  let allPassed = true
  for (const check of checks) {
    if (check.pattern.test(destContent)) {
      console.log('[verify-preload] ✓ Check passed:', check.desc)
    } else {
      console.warn('[verify-preload] ✗ Check failed:', check.desc)
      if (check.desc !== ' CommonJS export (optional)') {
        allPassed = false
      }
    }
  }
  
  if (allPassed) {
    console.log('[verify-preload] All checks passed! window.api should be available.')
    process.exit(0)
  } else {
    console.error('[verify-preload] Some checks failed!')
    process.exit(1)
  }
}

verifyPreload()
