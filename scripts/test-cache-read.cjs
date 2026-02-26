const { _electron } = require('playwright-core');
const path = require('path');

async function test() {
  const electronApp = await _electron.launch({
    args: [
      path.join(__dirname, '../dist-electron/main/index.js'),
      '--no-sandbox'
    ],
  });

  try {
    // 在主进程中执行代码
    const result = await electronApp.evaluate(async ({ app }) => {
      // 这里需要访问 databaseService，但无法直接访问
      // 只能通过 IPC 调用暴露的方法
      return { message: 'Cannot access main process internals directly' };
    });
    
    console.log(result);
    
  } finally {
    await electronApp.close();
  }
}

test().catch(console.error);
