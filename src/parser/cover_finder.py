"""Cover finder for anime from Bangumi website."""
import json
import re
from typing import Dict, List, Optional, Any

from bs4 import BeautifulSoup

from ..config import (
    BANGUMI_SEARCH_URL,
    BANGUMI_RESULT_LIMIT,
    BANGUMI_BASE_URL,
    WIKIPEDIA_SEARCH_URL,
    WIKIPEDIA_BASE_URL,
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

# Maximum search keyword length (Bangumi works better with shorter queries)
MAX_KEYWORD_LENGTH = 15


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

        Search strategy:
        1. Try both traditional and simplified Chinese, merge results
        2. Score all results using original title, pick best match
        3. Try core keyword search if no good match
        4. Try Wikipedia search as fallback

        Args:
            title: Anime title to search.
            include_details: If True, include subject URL and other details.

        Returns:
            Dict with cover_url, score, and optionally subject_url, or None.
        """
        # Collect all results from different search variants
        all_results = []

        # Strategy 1: Try both traditional and simplified Chinese searches
        # and merge results for best match selection
        title_simplified = self._to_simplified_chinese(title)

        # Search with original (traditional) title
        original_results = self._search_with_keyword_multi(title, include_details)
        all_results.extend(original_results)

        # Search with simplified title if different
        if title_simplified and title_simplified != title:
            simplified_results = self._search_with_keyword_multi(title_simplified, include_details,
                                                                  original_title=title)
            all_results.extend(simplified_results)

        # Find best result from all merged results
        if all_results:
            best_result = self._pick_best_result(title, all_results)
            if best_result:
                return best_result

        # Strategy 2: Try core keywords if full title failed
        core_keywords = self._extract_core_keywords(title)
        if core_keywords and core_keywords != title:
            core_results = self._search_with_keyword_multi(core_keywords, include_details,
                                                           original_title=title)
            if core_results:
                best_result = self._pick_best_result(title, core_results)
                if best_result:
                    return best_result

        # Strategy 3: Try Wikipedia search as fallback
        result = self._search_wikipedia(title, include_details)
        if result:
            return result

        return None

    def _search_with_keyword_multi(self, keyword: str, include_details: bool = False,
                                    original_title: Optional[str] = None) -> list:
        """Search Bangumi with keyword and return multiple results with scores.

        Args:
            keyword: Search keyword.
            include_details: If True, include subject URL.
            original_title: Original title for similarity comparison.

        Returns:
            List of result dicts with cover_url, title, subject_url, and score.
        """
        if not keyword:
            return []

        encoded_keyword = re.sub(PATTERNS["non_word_chars"], "", keyword).strip()
        if not encoded_keyword:
            return []

        url = self._bangumi_url.format(keyword=encoded_keyword)
        try:
            html = self.client.get(url)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("li.item")

            if not items:
                return []

            # Use original_title for comparison if provided, otherwise use keyword
            compare_title = original_title if original_title else keyword

            # If keyword is simplified Chinese and different from original_title,
            # also convert compare_title to simplified for better character overlap
            if original_title and keyword != original_title:
                compare_title_simplified = self._to_simplified_chinese(original_title)
                if compare_title_simplified:
                    compare_title = compare_title_simplified

            return self._score_all_results(compare_title, items, include_details)
        except Exception:
            return []

    def _score_all_results(self, original_title: str, items: list,
                           include_details: bool = False) -> list:
        """Score all search results and return sorted list.

        Args:
            original_title: Original anime title for comparison.
            items: List of Bangumi search result items.
            include_details: If True, include subject URL.

        Returns:
            List of result dicts sorted by score (highest first).
        """
        results = []

        for item in items:
            name_elem = item.select_one("h3 a")
            result_name = name_elem.get_text(strip=True) if name_elem else ""

            if not result_name:
                continue

            # Skip results that are too short (likely wrong matches like single character titles)
            result_name_clean = re.sub(PATTERNS["non_word_chars"], "", result_name).strip()
            if len(result_name_clean) < MIN_TITLE_LENGTH:
                # Give a very low score to very short titles
                score = 0
            else:
                # Calculate similarity score
                score = self._calculate_title_similarity(original_title, result_name)

            # Extract cover URL
            cover_url = self._extract_cover_from_item(item)
            if not cover_url:
                continue

            # Extract subject URL
            subject_url = None
            if include_details and name_elem:
                href = name_elem.get("href", "")
                if href:
                    subject_url = BANGUMI_BASE_URL + href

            results.append({
                "cover_url": cover_url,
                "title": result_name,
                "subject_url": subject_url,
                "score": score
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _pick_best_result(self, original_title: str, results: list) -> Optional[dict]:
        """Pick the best matching result from scored results.

        Args:
            original_title: Original anime title.
            results: List of scored results.

        Returns:
            Best matching result or None if no good match found.
        """
        if not results:
            return None

        # Sort by score descending to get the best match first
        sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

        # Find best result that meets minimum score threshold
        for result in sorted_results:
            if result.get("score", 0) >= MIN_MATCH_SCORE:
                return result

        # If no result meets threshold, return the top result but with lower confidence
        # This allows fallback to first result when no good match exists
        if sorted_results:
            sorted_results[0]["score"] = 0  # Mark as low confidence
            return sorted_results[0]

        return None

    def _to_simplified_chinese(self, text: str) -> str:
        """Convert Traditional Chinese to Simplified Chinese.

        Uses hanziconv library for conversion.

        Args:
            text: Traditional Chinese text.

        Returns:
            Simplified Chinese text.
        """
        if not text:
            return ""

        # Try using hanziconv if available
        try:
            from hanziconv import HanziConv
            return HanziConv.toSimplified(text)
        except ImportError:
            # If hanziconv is not available, return original text
            return text

    def _search_wikipedia(self, title: str, include_details: bool = False) -> Optional[dict]:
        """Search Wikipedia for anime info as fallback.

        Args:
            title: Anime title to search.
            include_details: If True, include subject URL.

        Returns:
            Dict with cover_url and title, or None if not found.
        """
        if not title:
            return None

        # URL encode the keyword
        from urllib.parse import quote
        encoded_keyword = quote(title, safe='')
        url = WIKIPEDIA_SEARCH_URL.format(keyword=encoded_keyword)

        try:
            html = self.client.get(url)
            soup = BeautifulSoup(html, "html.parser")

            # Try to find the first result link
            result_link = soup.select_one('div.mw-search-result-heading a')
            if not result_link:
                return None

            result_title = result_link.get_text(strip=True)
            result_url = WIKIPEDIA_BASE_URL + result_link.get('href', '')

            # Fetch the article page to get the cover image
            article_html = self.client.get(result_url)
            article_soup = BeautifulSoup(article_html, "html.parser")

            # Try to find the featured image or first image in the infobox
            cover_url = None

            # Try to find image in infobox
            infobox = article_soup.select_one('table.infobox')
            if infobox:
                # Try to find the first image in infobox
                first_img = infobox.select_one('img')
                if first_img:
                    src = first_img.get('src', '')
                    if src:
                        cover_url = self._normalize_cover_url(src)

            # Try to find file link for the main image
            if not cover_url:
                file_link = article_soup.select_one('a.image[href*="File:"]')
                if file_link:
                    # Try to find the image in the file page
                    file_href = file_link.get('href', '')
                    if file_href:
                        file_url = WIKIPEDIA_BASE_URL + file_href
                        file_html = self.client.get(file_url)
                        file_soup = BeautifulSoup(file_html, "html.parser")
                        img = file_soup.select_one('img[typeof="mw:File"]') or file_soup.select_one('div#file img')
                        if img:
                            src = img.get('src', '') or img.get('data-src', '')
                            if src:
                                cover_url = self._normalize_wikipedia_url(src)

            return {
                "cover_url": cover_url,
                "title": result_title,
                "subject_url": result_url
            }
        except Exception:
            return None

    def _normalize_wikipedia_url(self, url: str) -> str:
        """Normalize Wikipedia image URL to get a larger version.

        Args:
            url: Wikipedia image URL.

        Returns:
            Normalized URL pointing to a larger image.
        """
        if not url:
            return ""

        # Wikipedia URLs often contain parameters, try to get a larger version
        # Example: //upload.wikimedia.org/wikipedia/commons/thumb/xxx/yyy/zzz.jpg/320px-zzz.jpg
        # We can try to increase the size by changing the thumbnail parameter

        if url.startswith('//'):
            url = 'https:' + url

        # Try to increase thumbnail size from 320px to 640px or original
        if '/thumb/' in url:
            # Remove the thumbnail size prefix
            url = re.sub(r'/thumb/([^/]+)/([^/]+)/([^/]+)/[^/]+$', r'/thumb/\1/\2/\3', url)
            # Remove the size suffix from filename
            url = re.sub(r'/\d+px-([^/]+)$', r'/\1', url)

        return url

    def _search_with_keyword(self, keyword: str, include_details: bool = False) -> Optional[dict]:
        """Search Bangumi with a specific keyword.

        Args:
            keyword: Search keyword.
            include_details: If True, include subject URL.

        Returns:
            Dict with cover_url and title, or None if no results.
        """
        if not keyword:
            return None

        encoded_keyword = re.sub(PATTERNS["non_word_chars"], "", keyword).strip()
        if not encoded_keyword:
            return None

        url = self._bangumi_url.format(keyword=encoded_keyword)
        try:
            html = self.client.get(url)
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("li.item")

            if not items:
                return None

            # Take the first result
            first_item = items[0]
            cover_url = self._extract_cover_from_item(first_item)
            if not cover_url:
                return None

            name_elem = first_item.select_one("h3 a")
            result_name = name_elem.get_text(strip=True) if name_elem else ""

            subject_url = None
            if include_details and name_elem:
                href = name_elem.get("href", "")
                if href:
                    subject_url = BANGUMI_BASE_URL + href

            return {
                "cover_url": cover_url,
                "title": result_name,
                "subject_url": subject_url
            }
        except Exception:
            return None

    def get_bangumi_info(self, anime: Anime, update_anime: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed Bangumi info for an anime, including cover.

        This method combines cover fetching and detailed info fetching into a single
        operation to avoid redundant network requests.

        Args:
            anime: Anime object to find info for.
            update_anime: If True, update the anime object with cover_url and match info.

        Returns:
            Dict with Bangumi info (cover_url, rating, rank, type, date, summary, etc.),
            or None if not found.
        """
        # First, search to find the best match and get subject URL
        search_result = self._search_bangumi(anime.title, include_details=True)
        if not search_result:
            return None

        subject_url = search_result.get("subject_url")
        cover_url = search_result.get("cover_url")

        # If we only need cover and don't need detailed info, return early
        if not subject_url:
            # Return just the cover info
            return {
                "cover_url": cover_url,
                "title": search_result.get("title"),
                "subject_url": None,
                "rating": None,
                "rank": None,
                "type": None,
                "date": None,
                "summary": None,
                "genres": [],
                "staff": [],
                "cast": []
            }

        try:
            # Fetch the subject detail page
            html = self.client.get(subject_url)
            soup = BeautifulSoup(html, "html.parser")

            # Parse the info
            info = self._parse_bangumi_subject(soup, search_result)

            # Also update the anime object with cover info if requested
            if update_anime and cover_url:
                anime.cover_url = cover_url
                anime.match_source = self.SOURCE_BANGUMI
                anime.match_score = search_result.get("score", 0)
                # Store in cover cache
                self._cover_cache[anime.title] = {
                    "cover_url": cover_url,
                    "score": search_result.get("score", 0)
                }

            # Store in Bangumi info cache
            self._bangumi_info_cache[anime.title] = info

            return info
        except Exception as e:
            logger.error(f"Error fetching Bangumi info for {anime.title}: {e}")
            # Even on error, return the basic info we got from search
            if cover_url:
                return {
                    "cover_url": cover_url,
                    "title": search_result.get("title"),
                    "subject_url": subject_url,
                    "rating": None,
                    "rank": None,
                    "type": None,
                    "date": None,
                    "summary": None,
                    "genres": [],
                    "staff": [],
                    "cast": []
                }
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

        # Extract core keywords (main title before brackets)
        core_keywords = self._extract_core_keywords(title)
        if core_keywords and core_keywords != title:
            variants.append(core_keywords)

        # Also try with truncated keywords (important for long titles)
        truncated = self._truncate_keywords(core_keywords or title)
        if truncated and truncated != title and truncated != core_keywords:
            variants.append(truncated)

        # Use text_converter if available
        try:
            from src.utils.text_converter import get_search_variants
            converter_variants = get_search_variants(title)
            for v in converter_variants:
                if v not in variants:
                    variants.append(v)
            # Also try converter variants with core keywords
            core_converter_variants = get_search_variants(core_keywords or title)
            for v in core_converter_variants:
                if v not in variants:
                    variants.append(v)
        except ImportError:
            pass

        return variants

    def _extract_core_keywords(self, title: str) -> str:
        """Extract core keywords from title.

        For titles like "地獄模式 ～喜歡挑戰...～", extract "地獄模式".
        Keeps season info like "第一季", "第二季".

        Args:
            title: Original title.

        Returns:
            Core keywords string.
        """
        if not title:
            return ""

        # Remove content inside brackets (full width and half width)
        # Keep season info (第一季, 第二季, etc.)
        core = re.sub(r"[【】\(\)（）\[\]～~].*$", "", title)
        core = core.strip()

        return core if core else title

    def _truncate_keywords(self, keywords: str) -> str:
        """Truncate keywords to maximum length for better search results.

        Args:
            keywords: Keywords string.

        Returns:
            Truncated keywords string.
        """
        if not keywords:
            return ""

        # Remove special characters first
        cleaned = re.sub(r"[【】\(\)（）\[\]～~!\！\?]", "", keywords)
        cleaned = cleaned.strip()

        if len(cleaned) <= MAX_KEYWORD_LENGTH:
            return cleaned

        # Truncate to max length, keeping complete words
        truncated = cleaned[:MAX_KEYWORD_LENGTH * 2]  # Allow some buffer

        # Find the last complete word boundary
        # Split by common delimiters
        import re as re_module
        parts = re_module.split(r"[\s,，、]", truncated)

        if len(parts) > 1:
            # Remove the last partial part
            result = " ".join(parts[:-1])
            if result:
                return result.strip()

        # If no good boundary found, just return first MAX_KEYWORD_LENGTH chars
        return cleaned[:MAX_KEYWORD_LENGTH]

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
        query_clean = re.sub(r"[【】\(\)（）\[\]!!！\s～~]", "", query).strip()
        result_clean = re.sub(r"[【】\(\)（）\[\]!!！\s～~]", "", result).strip()

        # Exact match (after cleaning)
        if query_clean == result_clean:
            return SCORE_EXACT

        # Check if result is contained in query or vice versa
        if query_clean in result_clean or result_clean in query_clean:
            return SCORE_SUBSTRING

        # Extract core (first part before brackets) for comparison
        query_core = self._extract_core_keywords(query_clean)
        result_core = self._extract_core_keywords(result_clean)

        # If cores match exactly, give high score
        if query_core and result_core and query_core == result_core:
            return SCORE_CONTAINS

        # If cores contain each other
        if query_core and result_core:
            if query_core in result_core or result_core in query_core:
                return SCORE_SUBSTRING - 5

        # Character-level overlap for Chinese/Japanese characters
        # This helps match titles in different languages
        c1 = set(c for c in query_clean if "\u4e00" <= c <= "\u9fff")
        c2 = set(c for c in result_clean if "\u4e00" <= c <= "\u9fff")

        if c1 and c2:
            # Calculate character overlap ratio
            overlap = len(c1 & c2)
            total = max(len(c1), len(c2))
            if total > 0:
                ratio = overlap / total
                # If high character overlap, return high score
                if ratio >= 0.5:
                    return int(ratio * SCORE_EXACT)
                elif ratio >= 0.3:
                    return int(ratio * SCORE_CONTAINS)
                elif ratio >= 0.2 and overlap >= 3:
                    return SCORE_CHINESE_OVERLAP

        # Word overlap (character-based for CJK)
        query_words = set(query_clean)
        result_words = set(result_clean)
        if query_words & result_words:
            overlap = len(query_words & result_words)
            total = len(query_words | result_words)
            if total > 0:
                ratio = overlap / total
                if ratio >= 0.3:
                    return int(ratio * SCORE_WORD_OVERLAP)

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
