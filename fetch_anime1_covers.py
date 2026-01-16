#!/usr/bin/env python3
"""
Anime1 番剧封面抓取脚本
用法: python3 fetch_anime1_covers.py

功能:
1. 从 Anime1 获取第一页番剧列表
2. 从 Bangumi 搜索获取封面 (优先)
3. 从 AniList 搜索获取封面 (备用)
4. 生成 markdown 文件
"""

import re
import urllib.request
import urllib.parse
import json
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装: pip install beautifulsoup4")
    exit(1)

try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
except ImportError:
    print("请安装: pip install deep-translator")
    exit(1)

# Bangumi 搜索接口
BANGUMI_SEARCH_URL = "https://bangumi.tv/subject_search/{keyword}?cat=2"

# AniList GraphQL endpoint
ANILIST_API = "https://graphql.anilist.co"

# 翻译缓存
_translation_cache = {}


def fetch_page(url):
    """获取网页内容 (自动处理Unicode URL)"""
    # 如果URL包含非ASCII字符，需要编码
    try:
        url.encode('ascii')
    except UnicodeEncodeError:
        url = urllib.parse.quote(url, safe=':/?=&')

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def translate_to_english(text):
    """翻译文本为日文 (日文标题在 AniList 匹配度更高)"""
    if not text or not re.search(r'[\u4e00-\u9fff]', text):
        return text  # 没有中文，直接返回

    # 检查缓存
    if text in _translation_cache:
        return _translation_cache[text]

    try:
        # 使用 MyMemory API 翻译为日文 (日文与 AniList 更匹配)
        translator = MyMemoryTranslator(source='zh-CN', target='ja')
        result = translator.translate(text)
        if result and result != text:
            _translation_cache[text] = result
            return result
    except Exception as e:
        pass

    try:
        # 备用: Google 翻译为日文
        translator = GoogleTranslator(source='zh-CN', target='ja')
        result = translator.translate(text)
        if result and result != text:
            _translation_cache[text] = result
            return result
    except Exception as e:
        pass

    return text


def extract_keywords(text):
    """从标题提取关键词用于搜索"""
    # 移除常见词
    stop_words = ['第二季', '第一季', '第三季', '第二', '第一', '第三', '可以幫忙',
                  '嗎', '?', '！', '為了', '的', '是', '我', '要', '在', '和', '與',
                  '被', '王子', '千金', '偶像', '公主', '教師', '教師']
    keywords = text
    for word in stop_words:
        keywords = keywords.replace(word, ' ')

    # 移除括号内容
    keywords = re.sub(r'[【】\(\)（）\[\]].*?[】\)）\]]', '', keywords)
    keywords = re.sub(r'[【】\(\)（）\[\]]', '', keywords)

    # 清理并提取中文词
    keywords = keywords.strip()
    return keywords if keywords else text


def extract_anime1_list(html):
    """从 Anime1 列表提取番剧信息"""
    pattern = r'<a href="(https://anime1\.me/(\d+))">([^<]+)\[(\d+)\]</a>'
    matches = re.findall(pattern, html)

    seen = set()
    result = []
    for url, cat_id, title, ep in matches:
        if cat_id not in seen and len(result) < 25:
            seen.add(cat_id)
            result.append({
                'title': title.strip(),
                'cat_id': cat_id,
                'detail_url': url,
                'episode': ep
            })
    return result


def search_anilist(query):
    """搜索 AniList 获取候选结果"""
    # Use simpler query format to avoid JSON encoding issues
    escaped_query = query.replace('"', '\\"')
    graphql_query = f"query {{ Page(perPage: 8) {{ media(search: \"{escaped_query}\", type: ANIME) {{ id title {{ romaji english native }} coverImage {{ large medium }} episodes }} }} }}"

    req = urllib.request.Request(
        ANILIST_API,
        data=json.dumps({"query": graphql_query}).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('data', {}).get('Page', {}).get('media', [])
    except Exception as e:
        print(f"  AniList API error: {e}")
        return []


def get_best_match(anime1_title, anime_list):
    """从 AniList 结果中找到最佳匹配"""
    if not anime_list:
        return None, 0, None

    best_match = None
    best_score = 0
    best_reason = None

    for media in anime_list:
        title = media.get('title', {})
        bgm_titles = [
            title.get('romaji', ''),
            title.get('english', ''),
            title.get('native', '')
        ]

        for bgm_title in bgm_titles:
            if not bgm_title:
                continue

            score, reason = match_title(anime1_title, bgm_title)
            if score > best_score:
                best_score = score
                best_match = media
                best_reason = reason

    return best_match, best_score, best_reason


def match_title(anime1_title, bgm_title):
    """检查标题匹配度 - 改进的模糊匹配"""
    if not bgm_title:
        return 0, None

    # 常用中日文字符映射 (中文 -> 日文)
    char_map = {
        '樂': '楽', '谷': '谷', '鳥': '鳥', '時': '時', '變': '変',
        '學': '学', '藥': '薬', '會': '会', '龍': '龍', '體': '体',
        '錢': '銭', '淚': '涙', '內': '内', '收': '収', '渚': '渚',
        '遥': '遥', '祈': '祈', '毅': '毅', '季': '期', '第二': '第',
        'M': 'M', 'I': 'I', 'V': 'V', 'E': 'E', 'S': 'S', 'A': 'A', 'L': 'L'
    }

    # 先提取英文词
    eng1_words = re.findall(r'[a-zA-Z]+', anime1_title.lower())
    eng2_words = re.findall(r'[a-zA-Z]+', bgm_title.lower())

    # 清理标题（用于中文比较）
    clean1 = re.sub(r'[【】\(\)（）0123456789第三季第二季一\s\-]', '', anime1_title)
    clean2 = re.sub(r'[【】\(\)（）\s\-]', '', bgm_title)

    # 尝试将中文标题中的字符转换为日文进行匹配
    clean1_mapped = clean1
    for cn, jp in char_map.items():
        clean1_mapped = clean1_mapped.replace(cn, jp)

    # 精确匹配
    if clean1 == clean2 or clean1_mapped == clean2:
        return 100, '精确'

    # 包含关系 (更宽松的检查)
    for c1 in [clean1, clean1_mapped]:
        if len(c1) >= 4 and len(clean2) >= 4:
            if c1 in clean2 or clean2 in c1:
                return 90, '包含'

    # 计算中文字符重叠度
    c1 = set(c for c in clean1 if '\u4e00' <= c <= '\u9fff')
    c2 = set(c for c in clean2 if '\u4e00' <= c <= '\u9fff')

    # 也检查映射后的字符
    c1_mapped = set(c for c in clean1_mapped if '\u4e00' <= c <= '\u9fff')

    # 使用最大的重叠
    all_c1 = c1 | c1_mapped
    if len(all_c1) >= 2 and len(c2) >= 2:
        overlap = len(all_c1 & c2)
        total = max(len(all_c1), len(c2))
        score = int(overlap / total * 100)
        if score >= 40:
            return score, '字符重叠'

    # 英文匹配 - 使用多种策略
    if len(eng1_words) >= 1 and len(eng2_words) >= 1:
        eng1_str = ''.join(eng1_words)
        eng2_str = ''.join(eng2_words)

        # 策略1: 子串匹配
        if len(eng1_str) >= 5 and len(eng2_str) >= 5:
            if eng1_str in eng2_str or eng2_str in eng1_str:
                return 85, '子串匹配'

        # 策略2: 单词重叠 (至少50%匹配)
        overlap = len(set(eng1_words) & set(eng2_words))
        total = max(len(set(eng1_words)), len(set(eng2_words)))
        if total > 0:
            score = int(overlap / total * 100)
            if score >= 50:
                return score, '英文匹配'

        # 策略3: 核心词匹配
        core1 = set(w for w in eng1_words if len(w) >= 5)
        core2 = set(w for w in eng2_words if len(w) >= 5)
        if core1 and core2:
            core_overlap = len(core1 & core2)
            if core_overlap > 0:
                return 60, '核心词匹配'

        # 策略4: 部分字符重叠
        for w1 in eng1_words:
            for w2 in eng2_words:
                if len(w1) >= 4 and len(w2) >= 4:
                    min_len = min(len(w1), len(w2))
                    overlap_chars = len(set(w1) & set(w2))
                    if overlap_chars / min_len >= 0.6:
                        return 55, '部分匹配'

    return 0, None


def search_bangumi(query):
    """从 Bangumi 搜索获取候选结果 - 使用 BeautifulSoup 解析"""
    # URL编码搜索关键词
    encoded_query = urllib.parse.quote(query)
    url = BANGUMI_SEARCH_URL.format(keyword=encoded_query)

    try:
        html = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        results = []

        # 找到所有搜索结果项
        items = soup.select('li.item')

        for item in items[:10]:
            # 获取封面图
            cover_link = item.select_one('a.subjectCover')
            if not cover_link:
                continue

            img = cover_link.select_one('img.cover')
            if not img:
                continue

            img_src = img.get('src', '')
            if not img_src:
                continue

            # 补全封面URL
            if img_src.startswith('//'):
                cover_url = 'https:' + img_src
            else:
                cover_url = img_src

            # 从链接提取 subject_id
            href = cover_link.get('href', '')
            subject_id_match = re.search(r'/subject/(\d+)', href)
            subject_id = subject_id_match.group(1) if subject_id_match else ''

            results.append({
                'subject_id': subject_id,
                'cover_url': cover_url
            })

        return results
    except Exception as e:
        print(f"  Bangumi API error: {e}")
        return []


def search_bangumi_with_title(query):
    """从 Bangumi 搜索获取候选结果 (包含标题) - 使用 BeautifulSoup 解析"""
    # URL编码搜索关键词
    encoded_query = urllib.parse.quote(query)
    url = BANGUMI_SEARCH_URL.format(keyword=encoded_query)

    try:
        html = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        results = []

        # 找到所有搜索结果项
        items = soup.select('li.item')

        for item in items[:10]:
            # 获取封面图
            cover_link = item.select_one('a.subjectCover')
            if not cover_link:
                continue

            img = cover_link.select_one('img.cover')
            if not img:
                continue

            img_src = img.get('src', '')
            if not img_src:
                continue

            # 补全封面URL
            if img_src.startswith('//'):
                cover_url = 'https:' + img_src
            else:
                cover_url = img_src

            # 获取标题
            title_link = item.select_one('h3 a.l')
            title = title_link.get_text(strip=True) if title_link else ''

            # 从链接提取 subject_id
            href = cover_link.get('href', '')
            subject_id_match = re.search(r'/subject/(\d+)', href)
            subject_id = subject_id_match.group(1) if subject_id_match else ''

            results.append({
                'subject_id': subject_id,
                'cover_url': cover_url,
                'title': title
            })

        return results
    except Exception as e:
        print(f"  Bangumi API error: {e}")
        return []


def main():
    print("=" * 60)
    print("Anime1 番剧封面抓取工具 (Bangumi + AniList)")
    print("=" * 60)

    # 1. 获取 Anime1 列表
    print("\n[1/4] 获取 Anime1 列表...")
    html = fetch_page("https://anime1.me/")
    anime_list = extract_anime1_list(html)
    print(f"    获取到 {len(anime_list)} 部番剧")

    # 2. 搜索 Bangumi 获取封面
    print("\n[2/4] 搜索 Bangumi 获取封面...")
    results = []

    for i, anime in enumerate(anime_list, 1):
        title = anime['title']
        print(f"    [{i}/{len(anime_list)}] {title[:25]}...", end=" ")

        # 先尝试 Bangumi 搜索 (原始中文标题)
        candidates = search_bangumi_with_title(title)
        candidates = [c for c in candidates if c]

        # 如果 Bangumi 没结果，尝试 AniList
        if not candidates:
            # 尝试翻译后搜索 AniList
            keywords = extract_keywords(title)
            if keywords != title:
                eng_keywords = translate_to_english(keywords)
                if eng_keywords != keywords:
                    candidates = search_anilist(eng_keywords)
                    candidates = [c for c in candidates if c]

            if not candidates:
                eng_title = translate_to_english(title)
                if eng_title != title:
                    candidates = search_anilist(eng_title)
                    candidates = [c for c in candidates if c]

        # 选择最佳结果
        if candidates:
            # Bangumi 结果有 cover_url key，AniList 有 coverImage key
            if 'cover_url' in candidates[0]:
                anime['cover'] = candidates[0].get('cover_url', '')
                anime['bgm_title'] = candidates[0].get('title', '')
                anime['subject_id'] = candidates[0].get('subject_id', '')
                anime['match_reason'] = 'Bangumi'
                anime['match_score'] = 100
                print("OK (Bangumi)")
            else:
                # AniList 结果
                best_match = candidates[0]
                cover_url = best_match.get('coverImage', {}).get('large') or best_match.get('coverImage', {}).get('medium')
                anime['cover'] = cover_url
                anime['bgm_title'] = best_match.get('title', {}).get('romaji') or best_match.get('title', {}).get('english')
                anime['subject_id'] = str(best_match.get('id', ''))
                anime['match_reason'] = 'AniList'
                anime['match_score'] = 50
                print("OK (AniList)")
        else:
            print("X")
            anime['match_score'] = 0

        results.append(anime)
        time.sleep(0.3)

    # 3. 统计
    matched = sum(1 for r in results if 'cover' in r and r['cover'])
    print(f"\n    成功匹配: {matched}/{len(results)}")

    # 4. 生成 markdown
    print("\n[3/4] 生成 markdown 文件...")

    md_content = """# Anime1.me 第一页番剧封面

封面来源: [Bangumi](https://bangumi.tv) | 数据来源: [Anime1.me](https://anime1.me)

---

## 2025-2026 冬季新番

| # | 番剧名 | 封面 | Anime1 | 集数 |
|---|--------|------|--------|------|
"""

    for i, anime in enumerate(results, 1):
        if anime.get('cover'):
            cover = f'<img src="{anime["cover"]}" width="150">'
        else:
            cover = '-'

        title = anime['title'][:22] + '...' if len(anime['title']) > 22 else anime['title']
        md_content += f"| {i} | {title} | {cover} | [链接]({anime['detail_url']}) | {anime['episode']} |\n"

    md_content += """
---

**辅助脚本**: `~/.claude/commands/fetch_anime1_covers.py`

更新日期: """ + time.strftime("%Y-%m-%d") + "\n"

    output_file = "/Users/gzp/.claude/commands/anime1-covers.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"    已保存到: {output_file}")

    # 5. 保存 JSON 数据
    print("\n[4/4] 保存 JSON 数据...")
    json_file = "/Users/gzp/.claude/commands/anime1_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"    已保存到: {json_file}")

    # 显示未匹配的番剧
    print("\n未匹配的番剧:")
    for anime in results:
        if not anime.get('cover'):
            print(f"  - {anime['title']}")

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
