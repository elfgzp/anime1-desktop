#!/usr/bin/env node

/**
 * Setup script for E2E tests
 * Run this before executing tests to ensure everything is ready
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔧 Setting up E2E tests...\n');

// Check if node_modules exists
const nodeModulesPath = path.join(__dirname, 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
  console.log('📦 Installing dependencies...');
  try {
    execSync('npm install', { stdio: 'inherit', cwd: __dirname });
    console.log('✅ Dependencies installed\n');
  } catch (error) {
    console.error('❌ Failed to install dependencies');
    process.exit(1);
  }
} else {
  console.log('✅ Dependencies already installed\n');
}

// Check if Playwright browsers are installed
console.log('🌐 Checking Playwright browsers...');
try {
  execSync('npx playwright install chromium', { stdio: 'inherit', cwd: __dirname });
  console.log('✅ Playwright browsers ready\n');
} catch (error) {
  console.error('❌ Failed to install Playwright browsers');
  process.exit(1);
}

// Check if frontend is built
const frontendDistPath = path.join(__dirname, '../frontend/dist');
if (!fs.existsSync(frontendDistPath)) {
  console.log('🏗️  Building frontend...');
  try {
    execSync('npm run build', { 
      stdio: 'inherit', 
      cwd: path.join(__dirname, '../frontend') 
    });
    console.log('✅ Frontend built\n');
  } catch (error) {
    console.error('❌ Failed to build frontend');
    process.exit(1);
  }
} else {
  console.log('✅ Frontend already built\n');
}

console.log('🎉 Setup complete! You can now run tests with:');
console.log('   npm test        # Run all tests');
console.log('   npm run test:ui # Run with UI');
