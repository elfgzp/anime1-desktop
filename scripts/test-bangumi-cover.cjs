const { findBangumiCover } = require('../dist-electron/main/index.js');

async function test() {
  try {
    console.log('Testing Bangumi cover lookup...');
    const result = await findBangumiCover('現在的是哪一個多聞！？', '2026');
    console.log('Result:', result);
    if (result.coverUrl) {
      console.log('Cover URL:', result.coverUrl);
      console.log('Has /l/:', result.coverUrl.includes('/l/'));
      console.log('Has /c/:', result.coverUrl.includes('/c/'));
    }
  } catch (e) {
    console.error('Error:', e);
  }
}

test();
