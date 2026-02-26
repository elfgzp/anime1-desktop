/**
 * E2E 测试环境检查脚本
 * 
 * 运行: npx ts-node --esm e2e/check-env.ts
 */
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'
import { spawn } from 'child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const checks: Array<{ description: string; path: string; exists: boolean; version?: string }> = []

async function checkFile(path: string, description: string): Promise<boolean> {
  const fullPath = resolve(__dirname, '..', path)
  const exists = existsSync(fullPath)
  checks.push({ description, path: fullPath, exists })
  return exists
}

async function checkElectron(): Promise<boolean> {
  return new Promise((resolve) => {
    const electronPath = resolve(__dirname, '../node_modules/.bin/electron')
    
    const electron = spawn(
      electronPath,
      ['--version'],
      { stdio: 'pipe' }
    )
    
    let output = ''
    electron.stdout.on('data', (data) => {
      output += data.toString()
    })
    
    electron.on('close', (code) => {
      const exists = code === 0
      checks.push({ 
        description: 'Electron 可执行', 
        path: 'electron --version', 
        exists,
        version: output.trim()
      })
      resolve(exists)
    })
    
    electron.on('error', () => {
      checks.push({ 
        description: 'Electron 可执行', 
        path: 'electron --version', 
        exists: false 
      })
      resolve(false)
    })
  })
}

async function main() {
  console.log('🔍 检查 E2E 测试环境...\n')
  
  // 检查必要的文件
  await checkFile('dist-electron/main/index.js', 'Electron Main 构建文件')
  await checkFile('dist-electron/preload/index.js', 'Electron Preload 构建文件')
  await checkFile('node_modules/.bin/electron', 'Electron 命令')
  await checkFile('node_modules/@playwright/test/package.json', 'Playwright 安装')
  
  // 检查 Electron 是否可用
  await checkElectron()
  
  // 打印结果
  console.log('检查结果:')
  console.log('='.repeat(60))
  
  let allPassed = true
  for (const check of checks) {
    const status = check.exists ? '✅' : '❌'
    console.log(`${status} ${check.description}`)
    console.log(`   路径: ${check.path}`)
    if (check.version) {
      console.log(`   版本: ${check.version}`)
    }
    console.log()
    
    if (!check.exists) {
      allPassed = false
    }
  }
  
  console.log('='.repeat(60))
  
  if (allPassed) {
    console.log('\n✅ 环境检查通过！可以运行 E2E 测试')
    console.log('\n运行测试:')
    console.log('  npm run test:e2e:sanity     # 最基本测试')
    console.log('  npm run test:e2e:smoke      # 冒烟测试')
    console.log('  npm run test:e2e:headed     # 有界面模式')
    console.log('  npm run test:e2e            # 完整测试')
  } else {
    console.log('\n❌ 环境检查未通过，请修复以下问题:')
    
    const missingBuild = checks.find(c => 
      c.description.includes('Main') && !c.exists
    )
    if (missingBuild) {
      console.log('\n  1. 缺少 Electron 构建文件，请运行:')
      console.log('     npm run build')
    }
    
    const missingModules = checks.find(c => 
      c.description.includes('命令') && !c.exists
    )
    if (missingModules) {
      console.log('\n  2. 缺少 node_modules，请运行:')
      console.log('     npm install')
    }
  }
  
  process.exit(allPassed ? 0 : 1)
}

main().catch(console.error)
