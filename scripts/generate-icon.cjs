#!/usr/bin/env node
/**
 * 生成多尺寸 ICO 文件
 */
const pngToIco = require('png-to-ico');
const fs = require('fs');
const path = require('path');

const sourcePng = path.join(__dirname, '../resources/icon.png');
const targetIco = path.join(__dirname, '../resources/icon.ico');

async function generate() {
  try {
    console.log('Generating icon.ico from icon.png...');
    const buf = await pngToIco(sourcePng);
    fs.writeFileSync(targetIco, buf);
    console.log('✅ Icon generated successfully:', targetIco);
  } catch (error) {
    console.error('❌ Failed to generate icon:', error);
    process.exit(1);
  }
}

generate();
