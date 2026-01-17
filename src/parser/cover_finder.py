"""Cover finder for anime from Bangumi website."""
import json
import re
from typing import Dict, List, Optional, Any

from bs4 import BeautifulSoup

from ..config import (
    BANGUMI_SEARCH_URL,
    BANGUMI_RESULT_LIMIT,
    BANGUMI_BASE_URL,
    MIN_MATCH_SCORE,
    MIN_TITLE_LENGTH,
    MIN_ENGLISH_LENGTH,
    MIN_CHINESE_CHARS,
    SCORE_EXACT,
    SCORE_CONTAINS,
    SCORE_SUBSTRING,
    SCORE_WORD_OVERLAP,
    SCORE_CHINESE_OVERLAP,
    STOP_WORDS,
    PATTERNS,
)
from ..models.anime import Anime
from ..utils.http import HttpClient


# ============================================
# Cover Finder Constants
# ============================================

# Match sources
SOURCE_BANGUMI = "Bangumi"

# URL normalization
URL_PREFIX_HTTPS = "https:"
URL_BANGUMI_BASE = "https://bangumi.tv"

# Thread pool
THREAD_POOL_WORKERS = 5

# Print formatting
PRINT_TITLE_TRUNCATE = 25


class CoverFinder:
    """Find anime covers from Bangumi website."""

    SOURCE_BANGUMI = SOURCE_BANGUMI

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        bangumi_url: str = BANGUMI_SEARCH_URL,
    ):
        """Initialize the cover finder.

        Args:
            http_client: Optional HTTP client instance.
            bangumi_url: Bangumi search URL pattern.
        """
        self.client = http_client or HttpClient()
        self._bangumi_url = bangumi_url
        # Cache for cover URLs (title -> cover_url)
        self._cover_cache = {}
        # Cache for Bangumi info (title -> info_dict)
        self._bangumi_info_cache = {}

    @property
    def bangumi_url(self) -> str:
        """Get Bangumi search URL."""
        return self._bangumi_url

    def find_cover_for_anime(self, anime: Anime) -> Anime:
        """Find cover for an anime from Bangumi.

        Args:
            anime: Anime object to find cover for.

        Returns:
            Updated Anime object with cover URL.
        """
        # Check cache first
        if anime.title in self._cover_cache:
            cached = self._cover_cache[anime.title]
            anime.cover_url = cached["cover_url"]
            anime.match_source = self.SOURCE_BANGUMI
            anime.match_score = cached["score"]
            return anime

        cover_info = self._search_bangumi(anime.title)
        if cover_info:
            anime.cover_url = cover_info["cover_url"]
            anime.match_source = self.SOURCE_BANGUMI
            anime.match_score = cover_info["score"]
            # Store in cache
            self._cover_cache[anime.title] = {
                "cover_url": cover_info["cover_url"],
                "score": cover_info["score"]
            }
        return anime

    def _search_bangumi(self, title: str, include_details: bool = False) -> Optional[dict]:
        """Search Bangumi for cover.

        Args:
            title: Anime title to search.
            include_details: If True, include subject URL and other details.

        Returns:
            Dict with cover_url, score, and optionally subject_url, or None.
        """
        # Try multiple search variants (simplified and traditional Chinese)
        search_variants = self._get_search_variants(title)
        results = []

        for variant in search_variants:
            keyword = self._extract_keywords(variant)
            if not keyword:
                continue

            encoded_keyword = re.sub(PATTERNS["non_word_chars"], "", keyword).strip()
            if not encoded_keyword:
                continue

            url = self._bangumi_url.format(keyword=encoded_keyword)
            try:
                html = self.client.get(url)
                soup = BeautifulSoup(html, "html.parser")
                items = soup.select("li.item")

                for item in items[:BANGUMI_RESULT_LIMIT]:
                    cover_url = self._extract_cover_from_item(item)
                    name_elem = item.select_one("h3 a")
                    result_name = name_elem.get_text(strip=True) if name_elem else ""

                    # Extract subject URL if requested
                    subject_url = None
                    if include_details and name_elem:
                        href = name_elem.get("href", "")
                        if href:
                            subject_url = BANGUMI_BASE_URL + href

                    # Calculate similarity score
                    score = self._calculate_title_similarity(variant, result_name)
                    if cover_url:
                        result = {
                            "cover_url": cover_url,
                            "score": score,
                            "title": result_name,
                            "variant": variant
                        }
                        if subject_url:
                            result["subject_url"] = subject_url
                        results.append(result)
            except Exception:
                continue

        if not results:
            return None

        # Return the best match, or the first result if all have low similarity
        # This handles cases where the anime title is in a different language
        # (e.g., English title on anime1.me, Chinese title on Bangumi)
        best = max(results, key=lambda x: x["score"])
        if best["score"] > 0:
            return {
                "cover_url": best["cover_url"],
                "score": best["score"],
                "title": best["title"],
                "subject_url": best.get("subject_url")
            }
        else:
            # All results have 0 similarity (different language)
            # Return the first result anyway
            return {
                "cover_url": results[0]["cover_url"],
                "score": SCORE_SUBSTRING,  # Use a lower score
                "title": results[0]["title"],
                "subject_url": results[0].get("subject_url")
            }

    def get_bangumi_info(self, anime: Anime) -> Optional[Dict[str, Any]]:
        """Get detailed Bangumi info for an anime.

        Args:
            anime: Anime object to find info for.

        Returns:
            Dict with Bangumi info (rating, rank, type, date, summary, etc.), or None.
        """
        # First, search to find the best match and get subject URL
        search_result = self._search_bangumi(anime.title, include_details=True)
        if not search_result or not search_result.get("subject_url"):
            return None

        subject_url = search_result["subject_url"]
        try:
            # Fetch the subject detail page
            html = self.client.get(subject_url)
            soup = BeautifulSoup(html, "html.parser")

            # Parse the info
            info = self._parse_bangumi_subject(soup, search_result)

            # Store in cache
            self._bangumi_info_cache[anime.title] = info

            return info
        except Exception as e:
            logger.error(f"Error fetching Bangumi info for {anime.title}: {e}")
            return None

    def _parse_bangumi_subject(self, soup: BeautifulSoup, search_result: dict) -> Dict[str, Any]:
        """Parse Bangumi subject page for detailed info.

        Args:
            soup: BeautifulSoup object of the subject page.
            search_result: Search result with cover_url and title.

        Returns:
            Dict with parsed info.
        """
        info = {
            "cover_url": search_result.get("cover_url"),
            "title": search_result.get("title"),
            "subject_url": search_result.get("subject_url"),
            "rating": None,
            "rank": None,
            "type": None,
            "date": None,
            "summary": None,
            "genres": [],
            "staff": [],
            "cast": []
        }

        # Rating: span[property='v:average']
        rating_elem = soup.select_one('span[property="v:average"]')
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                info["rating"] = float(rating_text)
            except ValueError:
                pass

        # Rank: small.alarm
        rank_elem = soup.select_one('small.alarm')
        if rank_elem:
            rank_text = rank_elem.get_text(strip=True).replace("#", "")
            try:
                info["rank"] = int(rank_text)
            except ValueError:
                pass

        # Type: from infobox (e.g., "TV", "剧场版")
        infobox = soup.select_one('#infobox')
        if infobox:
            # Find type in infobox - look for items like "话数", "放送开始"
            for li in infobox.select('li'):
                tip = li.select_one('.tip')
                if tip:
                    label = tip.get_text(strip=True)
                    # 放送开始日期
                    if '放送开始' in label:
                        date_text = li.get_text(strip=True).replace(label, '').strip()
                        info["date"] = date_text

        # Summary: div[property='v:summary']
        summary_elem = soup.select_one('div[property="v:summary"]')
        if summary_elem:
            summary = summary_elem.get_text(strip=True)
            # Remove © Bangumi footer if present
            summary = re.sub(r"©\s*Bangumi.*", "", summary).strip()
            info["summary"] = summary if summary else None

        # Parse staff from infobox
        if infobox:
            staff_map = {}
            for li in infobox.select('li'):
                tip = li.select_one('.tip')
                if tip:
                    label = tip.get_text(strip=True).rstrip(':')
                    # Skip non-staff fields
                    if label in ['中文名', '话数', '放送开始', '放送星期']:
                        continue
                    # Get text content, excluding links
                    content = li.get_text(strip=True).replace(tip.get_text(strip=True), '').strip()
                    # Remove extra whitespace
                    content = re.sub(r'\s+', ' ', content)
                    if content and content not in ['--', '—']:
                        # Handle multiple names separated by commas or顿号
                        names = re.split(r'[,，、／/]', content)
                        for name in names:
                            name = name.strip()
                            if name:
                                if label not in staff_map:
                                    staff_map[label] = []
                                if name not in staff_map[label]:
                                    staff_map[label].append(name)

            # Convert to staff list format
            for role, names in staff_map.items():
                for name in names[:3]:  # Limit to 3 names per role
                    info["staff"].append({"role": role, "name": name})

        return info

    def _get_search_variants(self, title: str) -> List[str]:
        """Get search keyword variants for different Chinese variants.

        Args:
            title: Original title.

        Returns:
            List of search variants.
        """
        variants = [title]

        # Use text_converter if available
        try:
            from src.utils.text_converter import get_search_variants
            converter_variants = get_search_variants(title)
            for v in converter_variants:
                if v not in variants:
                    variants.append(v)
        except ImportError:
            pass

        return variants

    def _calculate_title_similarity(self, query: str, result: str) -> int:
        """Calculate similarity score between query and result title.

        Args:
            query: Original search query.
            result: Bangumi result title.

        Returns:
            Similarity score (0-100).
        """
        if not query or not result:
            return 0

        # Remove special characters for comparison (including spaces)
        query_clean = re.sub(r"[【】\(\)（）\[\]!!！\s]", "", query).strip()
        result_clean = re.sub(r"[【】\(\)（）\[\]!!！\s]", "", result).strip()

        # Exact match (after cleaning)
        if query_clean == result_clean:
            return SCORE_EXACT

        # Check if result is contained in query or vice versa
        if query_clean in result_clean or result_clean in query_clean:
            return SCORE_SUBSTRING

        # Word overlap
        query_words = set(query_clean)
        result_words = set(result_clean)
        if query_words & result_words:
            overlap = len(query_words & result_words) / len(query_words | result_words)
            return int(overlap * SCORE_WORD_OVERLAP)

        return 0

    def _extract_cover_from_item(self, item) -> Optional[str]:
        """Extract cover URL from a Bangumi item.

        Args:
            item: BeautifulSoup item element.

        Returns:
            Cover URL or None.
        """
        cover_link = item.select_one("a.subjectCover")
        if not cover_link:
            return None

        img = cover_link.select_one("img.cover")
        if not img:
            return None

        img_src = img.get("src", "")
        if not img_src:
            return None

        return self._normalize_cover_url(img_src)

    def _normalize_cover_url(self, url: str) -> str:
        """Normalize cover URL to absolute URL.

        Args:
            url: URL string (may be relative).

        Returns:
            Absolute URL string.
        """
        if url.startswith("//"):
            return URL_PREFIX_HTTPS + url
        elif url.startswith("/"):
            return URL_BANGUMI_BASE + url
        return url

    def _find_best_match(self, anime1_title: str, results: list) -> Optional[dict]:
        """Find the best matching anime from search results.

        Args:
            anime1_title: Original title from Anime1.
            results: List of search results from Bangumi.

        Returns:
            Best matching result or None.
        """
        best_match = None
        best_score = 0

        for result in results:
            bgm_titles = [
                result.get("name", ""),
                result.get("name_cn", ""),
            ]

            for bgm_title in bgm_titles:
                if not bgm_title:
                    continue

                score = self._calculate_match_score(anime1_title, bgm_title)
                if score > best_score:
                    best_score = score
                    best_match = result

        return best_match if best_score >= MIN_MATCH_SCORE else None

    def _calculate_match_score(self, title1: str, title2: str) -> int:
        """Calculate match score between two titles.

        Args:
            title1: First title.
            title2: Second title.

        Returns:
            Match score (0-100).
        """
        if not title1 or not title2:
            return 0

        # Clean titles
        clean1 = re.sub(PATTERNS["clean_title"], "", title1)
        clean2 = re.sub(PATTERNS["clean_title2"], "", title2)

        # Exact match
        if clean1 == clean2:
            return SCORE_EXACT

        # Contains match
        if len(clean1) >= MIN_TITLE_LENGTH and len(clean2) >= MIN_TITLE_LENGTH:
            if clean1 in clean2 or clean2 in clean1:
                return SCORE_CONTAINS

        # Extract and compare English words
        eng1_words = re.findall(PATTERNS["english_words"], title1.lower())
        eng2_words = re.findall(PATTERNS["english_words"], title2.lower())

        if eng1_words and eng2_words:
            score = self._score_english_words(eng1_words, eng2_words)
            if score > 0:
                return score

        # Chinese character overlap
        score = self._score_chinese_chars(clean1, clean2)
        return score

    def _score_english_words(self, eng1_words: list, eng2_words: list) -> int:
        """Score based on English word overlap.

        Args:
            eng1_words: English words from title1.
            eng2_words: English words from title2.

        Returns:
            Match score.
        """
        eng1_str = "".join(eng1_words)
        eng2_str = "".join(eng2_words)

        # Substring match
        if len(eng1_str) >= MIN_ENGLISH_LENGTH and len(eng2_str) >= MIN_ENGLISH_LENGTH:
            if eng1_str in eng2_str or eng2_str in eng1_str:
                return SCORE_SUBSTRING

        # Word overlap
        overlap = len(set(eng1_words) & set(eng2_words))
        total = max(len(set(eng1_words)), len(set(eng2_words)))
        if total > 0:
            score = int(overlap / total * 100)
            if score >= SCORE_WORD_OVERLAP:
                return score

        return 0

    def _score_chinese_chars(self, clean1: str, clean2: str) -> int:
        """Score based on Chinese character overlap.

        Args:
            clean1: Cleaned title1.
            clean2: Cleaned title2.

        Returns:
            Match score.
        """
        c1 = set(c for c in clean1 if "\u4e00" <= c <= "\u9fff")
        c2 = set(c for c in clean2 if "\u4e00" <= c <= "\u9fff")

        if len(c1) >= MIN_CHINESE_CHARS and len(c2) >= MIN_CHINESE_CHARS:
            overlap = len(c1 & c2)
            total = max(len(c1), len(c2))
            score = int(overlap / total * 100)
            if score >= SCORE_CHINESE_OVERLAP:
                return score

        return 0

    def _extract_keywords(self, title: str) -> str:
        """Extract search keywords from title.

        Args:
            title: Original title.

        Returns:
            Extracted keywords.
        """
        keywords = title
        for word in STOP_WORDS:
            keywords = keywords.replace(word, " ")

        # Remove bracket content
        keywords = re.sub(PATTERNS["bracket_content"], "", keywords)
        keywords = re.sub(PATTERNS["brackets"], "", keywords)

        return keywords.strip()

    def find_covers_batch(self, anime_list: List[Anime]) -> List[Anime]:
        """Find covers for multiple anime (parallel).

        Args:
            anime_list: List of Anime objects.

        Returns:
            Updated list of Anime objects with covers.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total = len(anime_list)
        results = [None] * total

        def fetch_cover(index_anime):
            index, anime = index_anime
            updated = self.find_cover_for_anime(anime)
            print("  [" + str(index + 1) + "/" + str(total) + "] " + anime.title[:PRINT_TITLE_TRUNCATE] + "...")
            return index, updated

        with ThreadPoolExecutor(max_workers=THREAD_POOL_WORKERS) as executor:
            futures = {executor.submit(fetch_cover, (i, a)): i for i, a in enumerate(anime_list)}
            for future in as_completed(futures):
                idx, updated_anime = future.result()
                results[idx] = updated_anime

        return results

    def close(self):
        """Close the HTTP client and clear cache."""
        self.client.close()
        self._cover_cache.clear()
        self._bangumi_info_cache.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
