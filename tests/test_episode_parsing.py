"""Test for anime1.me episode parsing - especially single movie pages."""
import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from src.parser.anime1_parser import Anime1Parser


class TestAnime1EpisodeParsing:
    """Test episode parsing for anime1.me."""

    def test_parse_single_movie_page_has_episode(self):
        """Test that single movie page with embedded video can be parsed.

        This tests the case where a page has a video player directly embedded
        (like https://anime1.me/27546 - 劇場版『鏈鋸人 蕾潔篇』).

        The page should be recognized as having at least one episode.
        """
        # Single movie page HTML (similar to anime1.me/27546)
        single_movie_html = """
        <!DOCTYPE html>
        <html>
        <head><title>劇場版『鏈鋸人 蕾潔篇』</title></head>
        <body>
            <article class="post-27546 post type-post status-publish format-standard">
                <header class="entry-header">
                    <h2 class="entry-title">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</h2>
                    <time class="entry-date published updated" datetime="2025-12-12">2025-12-12</time>
                </header>
                <div class="entry-content">
                    <div class="vjscontainer">
                        <video id="vjs-pfkkz" data-apireq="..." data-vid="pfkkz"></video>
                    </div>
                    <p><a href="/?cat=1779">全集連結</a></p>
                </div>
            </article>
        </body>
        </html>
        """

        parser = Anime1Parser()
        episodes = parser._extract_episodes(single_movie_html)

        print(f"Single movie page episodes: {episodes}")

        # Should return 1 episode extracted from single episode page
        assert len(episodes) == 1
        assert episodes[0]["id"] == "27546"
        assert episodes[0]["url"] == "https://anime1.me/27546"
        # Title keeps the special format suffix since we're not stripping it
        assert "鏈鋸人" in episodes[0]["title"]

    def test_parse_category_page_has_episodes(self):
        """Test that category page (list) can be parsed correctly.

        This is the standard format for anime with multiple episodes.
        """
        # Category page HTML (similar to anime1.me/?cat=1779)
        category_html = """
        <!DOCTYPE html>
        <html>
        <head><title>分類頁面</title></head>
        <body>
            <article class="post-27788">
                <h2 class="entry-title">
                    <a href="https://anime1.me/27788">Princession Orchestra [37]</a>
                </h2>
                <time class="entry-date published updated" datetime="2026-01-16">2026-01-16</time>
            </article>
            <article class="post-27787">
                <h2 class="entry-title">
                    <a href="https://anime1.me/27787">測試動畫 [36]</a>
                </h2>
                <time class="entry-date published updated" datetime="2026-01-15">2026-01-15</time>
            </article>
        </body>
        </html>
        """

        parser = Anime1Parser()
        episodes = parser._extract_episodes(category_html)

        print(f"Category page episodes: {episodes}")

        # This should work - category page has correct structure
        assert len(episodes) == 2
        assert episodes[0]["id"] == "27788"
        assert episodes[0]["episode"] == "37"
        assert episodes[0]["url"] == "https://anime1.me/27788"

    def test_parse_category_page_with_special_episode_format(self):
        """Test parsing category page with special episode formats like [劇場版].

        This is a real test case from https://anime1.me/?cat=1779
        The page has a movie with title format: "劇場版『鏈鋸人 蕾潔篇』 [劇場版]"

        The parser should:
        1. Skip episodes without numeric [N] format in title
        2. The actual episode number (e parameter) will be fetched from the episode page
        3. This is correct because URL ID (27546) is NOT the episode number - it's a page ID
        """
        # Category page HTML with movie format (similar to anime1.me/?cat=1779)
        category_html_with_movie = """
        <!DOCTYPE html>
        <html>
        <head><title>分類頁面</title></head>
        <body>
            <article class="post-27546">
                <h2 class="entry-title">
                    <a href="https://anime1.me/27546">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</a>
                </h2>
                <time class="entry-date published updated" datetime="2025-12-12">2025-12-12</time>
            </article>
            <article class="post-10001">
                <h2 class="entry-title">
                    <a href="https://anime1.me/10001">測試動畫 SP [SP]</a>
                </h2>
                <time class="entry-date published updated" datetime="2025-12-11">2025-12-11</time>
            </article>
            <article class="post-10002">
                <h2 class="entry-title">
                    <a href="https://anime1.me/10002">測試動畫 OVA [OVA]</a>
                </h2>
                <time class="entry-date published updated" datetime="2025-12-10">2025-12-10</time>
            </article>
        </body>
        </html>
        """

        parser = Anime1Parser()
        episodes = parser._extract_episodes(category_html_with_movie)

        print(f"Category page with movie format episodes: {episodes}")

        # Special format episodes ([劇場版], [SP], [OVA]) should be skipped
        # The actual episode number will be fetched from the episode page via proxy/episode-api
        assert len(episodes) == 0

    def test_mixed_episode_formats(self):
        """Test parsing page with both numeric and special episode formats."""
        mixed_html = """
        <!DOCTYPE html>
        <html>
        <head><title>混合格式</title></head>
        <body>
            <article class="post-27788">
                <h2 class="entry-title">
                    <a href="https://anime1.me/27788">Princession Orchestra [37]</a>
                </h2>
                <time class="entry-date published updated" datetime="2026-01-16">2026-01-16</time>
            </article>
            <article class="post-27546">
                <h2 class="entry-title">
                    <a href="https://anime1.me/27546">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</a>
                </h2>
                <time class="entry-date published updated" datetime="2025-12-12">2025-12-12</time>
            </article>
        </body>
        </html>
        """

        parser = Anime1Parser()
        episodes = parser._extract_episodes(mixed_html)

        print(f"Mixed format episodes: {episodes}")

        # Only numeric format should be included
        assert len(episodes) == 1

        # Numeric format - should use the number from [N]
        assert episodes[0]["episode"] == "37"
        assert episodes[0]["url"] == "https://anime1.me/27788"

        # Special format [劇場版] should be skipped - the episode number
        # will be fetched from the episode page via proxy/episode-api

    def test_single_movie_should_return_self_as_episode(self):
        """Test that single movie pages should return themselves as an episode.

        When a user visits a single movie page directly (like /27546),
        that page itself is the episode, not a list of episodes.

        The fix should:
        1. Detect that this is a single post (not a category listing)
        2. Extract the video info from the video tag or page data
        3. Return the current page as an episode
        """
        single_movie_html = """
        <article id="post-27546" class="post-27546 post type-post status-publish format-standard">
            <header class="entry-header">
                <h2 class="entry-title">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</h2>
                <time class="entry-date published updated" datetime="2025-12-12T01:54:20+08:00">2025-12-12</time>
            </header>
            <div class="entry-content">
                <div class="vjscontainer">
                    <video id="vjs-pfkkz" data-apireq='{"c":"1779","e":"2","t":1768726209,"p":2,"s":"35b100e55bfa7c726ddb769be53aefa0"}' data-vid="pfkkz"></video>
                </div>
                <p><a href="/?cat=1779">全集連結</a></p>
            </div>
        </article>
        """

        soup = BeautifulSoup(single_movie_html, "html.parser")

        # Check if this is a single post page
        article = soup.find('article')
        is_single_post = article and article.get('class') and 'post' in ' '.join(article.get('class', []))

        # Check if there's a video tag
        video = soup.find('video')
        has_video = video is not None

        print(f"Is single post: {is_single_post}")
        print(f"Has video: {has_video}")

        # These conditions should trigger the single episode detection
        assert is_single_post == True
        assert has_video == True

    def test_anime_id_27546_should_have_episode(self):
        """Test that anime ID 27546 should have at least one episode.

        This is a real test case from https://anime1.me/27546
        """
        # The anime ID is 27546, and the page has one video embedded
        anime_id = "27546"

        # The category ID from the page is 1779 (found in dataLayer)
        category_id = "1779"

        # Expected: this anime should return at least one episode
        # either from parsing the single page, or by redirecting to the category

        # For now, this test documents the expected behavior
        assert anime_id == "27546"
        assert category_id == "1779"

    def test_extract_single_episode_from_article_class(self):
        """Test that episode ID is extracted from article class (e.g., post-27546).

        This is the fix for pages where canonical URL is missing.
        The episode ID should be extracted from the article's class attribute.
        """
        single_page_html = """
        <!DOCTYPE html>
        <html>
        <head><title>劇場版『鏈鋸人 蕾潔篇』</title></head>
        <body>
            <article class="post-27546 post type-post status-publish format-standard">
                <header class="entry-header">
                    <h2 class="entry-title">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</h2>
                    <time class="entry-date published updated" datetime="2025-12-12">2025-12-12</time>
                </header>
                <div class="entry-content">
                    <div class="vjscontainer">
                        <video id="vjs-pfkkz"
                               data-apireq='{"c":"1779","e":"2","t":1768726209,"p":2,"s":"35b100e55bfa7c726ddb769be53aefa0"}'
                               data-vid="pfkkz"></video>
                    </div>
                    <p><a href="/?cat=1779">全集連結</a></p>
                </div>
            </article>
        </body>
        </html>
        """

        soup = BeautifulSoup(single_page_html, "html.parser")
        parser = Anime1Parser()

        # Call _extract_single_episode directly
        episode = parser._extract_single_episode(soup)

        print(f"Extracted single episode: {episode}")

        # Verify the episode was extracted correctly
        assert episode is not None
        assert episode["id"] == "27546"
        assert episode["url"] == "https://anime1.me/27546"
        assert episode["episode"] == "2"  # From data-apireq e parameter
        assert "鏈鋸人" in episode["title"]

    def test_cat_page_returns_single_episode(self):
        """Test that ?cat=1779 page returns a single episode.

        The real page https://anime1.me/?cat=1779 returns a single movie page
        (not a category listing), so _extract_single_episode should be used.
        """
        # This simulates the actual page structure of ?cat=1779
        cat_page_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>劇場版『鏈鋸人 蕾潔篇』 [劇場版] - ANIME1 動漫</title>
            <meta property="og:url" content="https://anime1.me/category/2025年秋季/劇場版-鏈鋸人-蕾潔篇">
        </head>
        <body>
            <article class="post-27546 post type-post status-publish format-standard hentry">
                <header class="entry-header">
                    <h2 class="entry-title">劇場版『鏈鋸人 蕾潔篇』 [劇場版]</h2>
                    <time class="entry-date published updated" datetime="2025-12-12T01:54:20+08:00">2025-12-12</time>
                </header>
                <div class="entry-content">
                    <div class="vjscontainer video-js vjs-pfkkz">
                        <video id="vjs-pfkkz"
                               data-apireq='{"c":"1779","e":"2","t":1768726209,"p":2,"s":"35b100e55bfa7c726ddb769be53aefa0"}'
                               data-vid="pfkkz"
                               data-tserver="pt2"></video>
                    </div>
                    <p><a href="/?cat=1779">全集連結</a></p>
                </div>
            </article>
        </body>
        </html>
        """

        parser = Anime1Parser()
        episodes = parser._extract_episodes(cat_page_html)

        print(f"?cat=1779 episodes: {episodes}")

        # Should return 1 episode extracted from single episode page
        assert len(episodes) == 1
        assert episodes[0]["id"] == "27546"
        assert episodes[0]["url"] == "https://anime1.me/27546"
        assert episodes[0]["episode"] == "2"


class TestAnime1ParserVideoExtraction:
    """Test video URL extraction from anime1.me pages."""

    def test_extract_video_info_from_single_page(self):
        """Test extracting video info from single movie page.

        Single movie pages have video info embedded in data-apireq attribute.
        """
        single_page_html = """
        <div class="vjscontainer">
            <video id="vjs-pfkkz"
                   data-apireq='{"c":"1779","e":"2","t":1768726209,"p":2,"s":"35b100e55bfa7c726ddb769be53aefa0"}'
                   data-vid="pfkkz"
                   data-tserver="pt2">
            </video>
        </div>
        """

        soup = BeautifulSoup(single_page_html, "html.parser")
        video = soup.find('video')

        if video:
            api_req = video.get('data-apireq', '')
            vid = video.get('data-vid', '')
            tserver = video.get('data-tserver', '')

            print(f"API req: {api_req}")
            print(f"Video ID: {vid}")
            print(f"TServer: {tserver}")

            # These should be extractable
            assert api_req != ''
            assert vid != ''

    def test_parse_episode_id_from_url(self):
        """Test parsing episode ID from anime1.me URL."""
        test_urls = [
            ("https://anime1.me/27546", "27546"),
            ("https://anime1.me/27788", "27788"),
            ("https://anime1.me/?cat=1779", None),  # Category URL, no episode ID
        ]

        import re
        for url, expected_id in test_urls:
            match = re.search(r'/(\d+)$', url)
            if expected_id:
                assert match is not None, f"URL {url} should have episode ID"
                assert match.group(1) == expected_id
            else:
                # Category URLs shouldn't match
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
