#!/usr/bin/env python3
"""测试 anime1.pw 页面解析

结论: anime1.pw 有 SSL 配置问题，Python requests 和 curl 都无法连接
     但浏览器（Safari/WebKit）可以正常访问
     解决方案: 通过前端 webview 获取页面内容，发送到后端解析
"""

import requests
from bs4 import BeautifulSoup
import re

# 禁用 SSL 验证警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 测试用 URL
TEST_PW_URL = "https://anime1.pw/?cat=58"  # SSL 有问题
TEST_ME_URL = "https://anime1.me/325"  # 可以访问

def test_page(url, name):
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"URL: {url}")
    print('='*60)

    try:
        print("\n1. 尝试直接 requests 获取...")
        response = requests.get(url, timeout=10, verify=False)
        print(f"   状态码: {response.status_code}")
        print(f"   内容长度: {len(response.text)}")

        if response.status_code != 200:
            print("   ❌ 请求失败")
            return None

        # 检查是否有 SSL 或内容问题
        if 'anime1' not in response.text.lower() and len(response.text) < 1000:
            print("   ⚠️  响应内容可能有问题")
            print(f"   前200字符: {response.text[:200]}")

        return response.text

    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL 错误: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 请求错误: {e}")
        return None

def parse_episodes(html, name):
    print(f"\n2. 解析 HTML 提取剧集...")
    if not html:
        print("   ❌ HTML 为空")
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # 查找剧集链接
    episodes = []

    # 方法1: 查找所有链接
    links = soup.find_all('a', href=True)
    print(f"   找到 {len(links)} 个链接")

    # 筛选剧集链接 (数字结尾的 URL)
    episode_pattern = re.compile(r'/(\d+)$')
    for link in links:
        href = link.get('href', '')
        text = link.get_text(strip=True)

        # 检查是否是剧集链接
        match = episode_pattern.search(href)
        if match and text:
            episode_num = match.group(1)
            if episode_num and text != '下一集':
                episodes.append({
                    'url': href,
                    'title': text,
                    'episode_id': episode_num
                })

    # 去重
    seen = set()
    unique_episodes = []
    for ep in episodes:
        key = ep['url']
        if key not in seen:
            seen.add(key)
            unique_episodes.append(ep)

    print(f"   找到 {len(unique_episodes)} 个唯一剧集")

    # 显示前5个
    for ep in unique_episodes[:5]:
        print(f"   - [{ep['episode_id']}] {ep['title'][:40]}")

    if len(unique_episodes) > 5:
        print(f"   ... 还有 {len(unique_episodes) - 5} 个")

    return unique_episodes

def find_video_player(html, name):
    print(f"\n3. 查找视频播放器...")
    if not html:
        print("   ❌ HTML 为空")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 查找 iframes
    iframes = soup.find_all('iframe')
    print(f"   找到 {len(iframes)} 个 iframe")

    for iframe in iframes[:3]:
        src = iframe.get('src', '')
        if src:
            print(f"   - iframe src: {src[:80]}...")

    # 查找 video 标签
    videos = soup.find_all('video')
    print(f"   找到 {len(videos)} 个 video 标签")

    # 查找 JavaScript 视频源
    scripts = soup.find_all('script')
    video_patterns = ['player', 'video', 'source', 'stream', 'cdn']
    for script in scripts[:5]:
        src = script.get('src', '')
        text = script.get_text()
        for pattern in video_patterns:
            if pattern in src.lower() or pattern in text.lower():
                print(f"   - 找到可能的视频相关脚本: {src[:60]}")
                break

    return iframes

def test_with_curl():
    print(f"\n{'='*60}")
    print("测试: 使用 curl 获取页面")
    print('='*60)

    import subprocess

    try:
        result = subprocess.run(
            ['curl', '-s', '-k', '-L', TEST_URL],
            capture_output=True,
            text=True,
            timeout=15
        )
        print(f"curl 退出码: {result.returncode}")
        print(f"内容长度: {len(result.stdout)}")

        if result.returncode == 0 and len(result.stdout) > 1000:
            # 检查内容
            if '草莓哀歌' in result.stdout:
                print("✅ curl 成功获取页面内容")
                return result.stdout
            else:
                print("⚠️  curl 返回内容可能不正确")
                print(f"前500字符: {result.stdout[:500]}")
        else:
            print(f"❌ curl 失败")
            print(f"stderr: {result.stderr[:500] if result.stderr else '无'}")

    except Exception as e:
        print(f"❌ curl 执行错误: {e}")

    return None

def test_anime1_me():
    """测试 anime1.me (可以正常访问的备用域名)"""
    print(f"\n{'='*60}")
    print("测试: anime1.me (备用域名，可正常访问)")
    print(f"URL: {TEST_ME_URL}")
    print('='*60)

    try:
        response = requests.get(TEST_ME_URL, timeout=10)
        print(f"\n状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)}")

        if response.status_code == 200:
            episodes = parse_episodes(response.text, "anime1.me")
            find_video_player(response.text, "anime1.me")
            return response.text
    except Exception as e:
        print(f"错误: {e}")
    return None

def main():
    print("=" * 60)
    print("Anime1.pw 页面测试")
    print("=" * 60)

    # 测试1: anime1.me (工作正常)
    html = test_anime1_me()

    # 测试2: anime1.pw (SSL 问题)
    print("\n" + "=" * 60)
    print("测试: anime1.pw (SSL 配置问题)")
    print(f"URL: {TEST_PW_URL}")
    print("预期: SSL 错误 - 无法通过 Python 连接")
    print('='*60)

    try:
        response = requests.get(TEST_PW_URL, timeout=10, verify=False)
        print(f"状态码: {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"SSL 错误 (预期): {type(e).__name__}")
        print("原因: anime1.pw 服务器 SSL 配置问题")
        print("解决方案: 通过前端 webview (Safari/WebKit) 获取页面")

    # 测试3: curl
    curl_html = test_with_curl()

    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)
    print("1. anime1.pw 有 SSL 配置问题，Python 无法直接连接")
    print("2. anime1.me (备用域名) 可以正常访问")
    print("3. 浏览器 (Safari/WebKit) 可以访问 anime1.pw")
    print("4. 解决方案: 通过 pywebview 前端获取 HTML，发送到后端解析")
    print("=" * 60)

if __name__ == '__main__':
    main()
