/**
 * Electron 调试脚本模板
 * 
 * 使用方法:
 * 1. 确保应用已运行: npm run dev
 * 2. 修改此脚本中的查询逻辑
 * 3. 运行: node scripts/debug-template.js
 */

const { chromium } = require('playwright-core');

async function debug() {
    console.log('Connecting to Electron...');
    
    try {
        const browser = await chromium.connectOverCDP('http://localhost:9222');
        const context = browser.contexts()[0];
        const page = context.pages()[0];
        
        console.log('Connected!');
        
        // ============ 在此处添加调试逻辑 ============
        
        // 示例 1: 截图
        await page.screenshot({ 
            path: 'screenshots/debug-' + Date.now() + '.png',
            fullPage: true 
        });
        console.log('Screenshot saved');
        
        // 示例 2: 检查元素
        const text = await page.locator('.anime-grid').innerText().catch(() => 'Not found');
        console.log('Anime grid text:', text.substring(0, 200));
        
        // 示例 3: 调用 API
        const result = await page.evaluate(async () => {
            try {
                const response = await window.api.anime.getList({ page: 1 });
                return { success: true, count: response.data?.animeList?.length };
            } catch (e) {
                return { success: false, error: e.message };
            }
        });
        console.log('API result:', result);
        
        // 示例 4: 检查 Store
        const storeInfo = await page.evaluate(() => {
            const pinia = window.__pinia;
            if (!pinia) return { error: 'Pinia not found' };
            
            const state = pinia.state.value;
            return {
                stores: Object.keys(state),
                animeCount: state.anime?.animeList?.length,
                favoriteCount: state.favorite?.favorites?.length
            };
        });
        console.log('Store info:', storeInfo);
        
        // ============================================
        
        await browser.close();
        console.log('Debug completed');
    } catch (err) {
        console.error('Debug failed:', err.message);
        console.log('\nMake sure:');
        console.log('1. App is running (npm run dev)');
        console.log('2. CDP is enabled (check DevTools listening on ws://localhost:9222)');
    }
}

debug();
