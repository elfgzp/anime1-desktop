/**
 * 手动功能验证脚本
 * 用于验证 IPC 功能和核心服务
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const MAIN_PATH = path.join(__dirname, 'dist-electron/main/index.js');

// 检查构建文件是否存在
function checkBuildFiles() {
  console.log('=== 检查构建文件 ===');
  
  const files = [
    'dist/index.html',
    'dist-electron/main/index.js',
    'dist-electron/preload/index.cjs'
  ];
  
  let allExist = true;
  for (const file of files) {
    const fullPath = path.join(__dirname, file);
    const exists = fs.existsSync(fullPath);
    console.log(`${exists ? '✅' : '❌'} ${file}`);
    if (!exists) allExist = false;
  }
  
  return allExist;
}

// 验证 IPC 频道白名单
function validateIPCChannels() {
  console.log('\n=== 验证 IPC 频道 ===');
  
  const preloadPath = path.join(__dirname, 'src/preload/index.cjs');
  const preloadContent = fs.readFileSync(preloadPath, 'utf-8');
  
  // 提取 validChannels
  const match = preloadContent.match(/const validChannels = \[([\s\S]*?)\]/);
  if (match) {
    const channels = match[1]
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.startsWith("'"))
      .map(line => line.replace(/['",]/g, ''));
    
    console.log(`✅ 找到 ${channels.length} 个 IPC 频道:`);
    
    // 分类显示
    const categories = {};
    for (const channel of channels) {
      const category = channel.split(':')[0];
      if (!categories[category]) categories[category] = [];
      categories[category].push(channel);
    }
    
    for (const [cat, chs] of Object.entries(categories)) {
      console.log(`  ${cat}: ${chs.length} 个`);
    }
    
    return channels;
  }
  
  return [];
}

// 验证类型定义
function validateTypeDefinitions() {
  console.log('\n=== 验证类型定义 ===');
  
  const apiTypesPath = path.join(__dirname, 'src/shared/types/api.ts');
  const content = fs.readFileSync(apiTypesPath, 'utf-8');
  
  // 统计接口数量
  const interfaces = content.match(/export interface \w+/g) || [];
  const types = content.match(/export type \w+/g) || [];
  
  console.log(`✅ API 类型定义:`);
  console.log(`  - Interfaces: ${interfaces.length}`);
  console.log(`  - Types: ${types.length}`);
  
  // 检查新添加的类型
  const newTypes = [
    'DeletePlaybackHistory',
    'GetPlaybackHistoryByAnime',
    'GetBatchPlaybackProgress',
    'ParsePwEpisodes'
  ];
  
  let hasNewTypes = true;
  for (const type of newTypes) {
    const exists = content.includes(type);
    console.log(`  ${exists ? '✅' : '❌'} ${type}`);
    if (!exists) hasNewTypes = false;
  }
  
  return hasNewTypes;
}

// 验证数据库方法
function validateDatabaseMethods() {
  console.log('\n=== 验证数据库方法 ===');
  
  const dbPath = path.join(__dirname, 'src/main/services/database/index.ts');
  const content = fs.readFileSync(dbPath, 'utf-8');
  
  const methods = [
    'deletePlaybackHistory',
    'getPlaybackHistoryByAnime',
    'getBatchPlaybackProgress'
  ];
  
  let allExist = true;
  for (const method of methods) {
    const exists = content.includes(method);
    console.log(`${exists ? '✅' : '❌'} ${method}`);
    if (!exists) allExist = false;
  }
  
  return allExist;
}

// 主函数
async function main() {
  console.log('🔍 Anime1 Desktop 功能验证\n');
  
  const results = {
    buildFiles: checkBuildFiles(),
    ipcChannels: validateIPCChannels().length > 0,
    typeDefinitions: validateTypeDefinitions(),
    databaseMethods: validateDatabaseMethods()
  };
  
  console.log('\n=== 验证结果 ===');
  for (const [name, passed] of Object.entries(results)) {
    console.log(`${passed ? '✅' : '❌'} ${name}`);
  }
  
  const allPassed = Object.values(results).every(v => v);
  
  if (allPassed) {
    console.log('\n✅ 所有验证通过！');
    process.exit(0);
  } else {
    console.log('\n❌ 部分验证失败');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('验证失败:', err);
  process.exit(1);
});
