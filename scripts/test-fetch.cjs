// 测试 Node.js fetch API 的 cookie 处理

async function testFetch() {
  // 1. 先访问首页
  console.log('1. 访问首页...');
  const homeResp = await fetch('https://anime1.me', {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
  });
  console.log('Home cookies:', homeResp.headers.get('set-cookie'));
  
  // 2. 访问剧集页面
  console.log('\n2. 访问剧集页面...');
  const epResp = await fetch('https://anime1.me/28159', {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Referer': 'https://anime1.me/?cat=1782'
    }
  });
  console.log('Episode status:', epResp.status);
  console.log('Episode cookies:', epResp.headers.get('set-cookie'));
  
  // 3. 调用视频 API
  console.log('\n3. 调用视频 API...');
  const postData = new URLSearchParams({
    d: JSON.stringify({ c: '1782', e: '9b', t: 1772076265, p: 0, s: 'test_signature' })
  });
  
  const apiResp = await fetch('https://d1zquzjgwo9yb.cloudfront.net/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Referer': 'https://anime1.me/28159',
      'Origin': 'https://anime1.me',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    body: postData.toString()
  });
  
  console.log('API status:', apiResp.status);
  console.log('API response:', await apiResp.text());
}

testFetch().catch(console.error);
