"""Anime1.me parser using BeautifulSoup4."""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from ..config import (
    ANIME1_BASE_URL,
    ANIME1_API_URL,
    PATTERNS,
    SEASONS,
    SUBTITLE_KEYWORDS,
    DEFAULTS,
)
from ..models.anime import Anime
from ..utils.http import HttpClient


class Anime1Parser:
    """Parser for Anime1.me website using JSON API."""

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        base_url: str = ANIME1_BASE_URL,
        api_url: str = ANIME1_API_URL,
    ):
        """Initialize the parser.

        Args:
            http_client: Optional HTTP client instance.
            base_url: Base URL for Anime1.me.
            api_url: JSON API URL for anime list.
        """
        self.client = http_client or HttpClient()
        self._base_url = base_url
        self._api_url = api_url

    @property
    def base_url(self) -> str:
        """Get base URL."""
        return self._base_url

    @property
    def api_url(self) -> str:
        """Get API URL."""
        return self._api_url

    def parse_page(self, page: int = DEFAULTS["page"]) -> List[Anime]:
        """Parse a page of anime listings.

        Args:
            page: Page number (1-indexed). Note: anime1.me API returns
                  all data, pagination is simulated by slicing.

        Returns:
            List of Anime objects.
        """
        url = self._api_url
        html = self.client.get(url)
        return self.parse_anime_list(html)

    def parse_anime_list(self, html: str) -> List[Anime]:
        """Parse anime list from JSON/HTML.

        Args:
            html: HTML content containing JSON data.

        Returns:
            List of Anime objects.
        """
        # Try to extract JSON data
        anime_list = self._extract_from_json(html)

        # Fallback: try regex pattern matching
        if not anime_list:
            anime_list = self._extract_from_regex(html)

        return anime_list

    def _extract_from_json(self, html: str) -> Optional[List[Anime]]:
        """Extract anime info from JSON data embedded in HTML.

        Args:
            html: HTML content.

        Returns:
            List of Anime objects or None.
        """
        try:
            import json as json_module

            # The JSON data is returned directly, not embedded
            data = json_module.loads(html)
            if not data:
                return None

            anime_list = []
            for item in data:
                if len(item) >= 2:
                    cat_id = str(item[0])
                    title_raw = str(item[1])

                    # Extract clean title (remove HTML tags but keep 🔞 marker)
                    # First remove the anchor tag but keep the content
                    title = re.sub(r'<a[^>]*>|</a>', '', title_raw)
                    title = title.strip()

                    # Skip if no title
                    if not title:
                        continue

                    # Extract episode from item[2] (format: "連載中(01)" or "(37)")
                    episode_str = str(item[2]) if len(item) > 2 else "0"
                    episode_match = re.search(r'\((\d+)\)', episode_str)
                    episode = int(episode_match.group(1)) if episode_match else 0

                    # Extract year, season, subtitle from item[3], item[4], item[5]
                    year = str(item[3]) if len(item) > 3 else ""
                    season = str(item[4]) if len(item) > 4 else ""
                    subtitle_group = str(item[5]) if len(item) > 5 else ""

                    # Build detail URL
                    if cat_id == "0" or not cat_id:
                        # External link to anime1.pw
                        link_match = re.search(r'href="([^"]+)"', title_raw)
                        if link_match:
                            detail_url = link_match.group(1)
                        else:
                            continue
                    else:
                        detail_url = f"{self._base_url}/?cat={cat_id}"

                    # Use cat_id or generate a unique id for external links
                    if cat_id == "0" or not cat_id:
                        # Generate unique ID from title hash
                        unique_id = str(abs(hash(title)) % 1000000)
                    else:
                        unique_id = cat_id

                    # Skip if already added
                    if any(a.id == unique_id for a in anime_list):
                        continue

                    anime_list.append(
                        Anime.create(
                            id=unique_id,
                            title=title,
                            detail_url=detail_url,
                            episode=episode,
                            year=year,
                            season=season,
                            subtitle_group=subtitle_group,
                        )
                    )

            return anime_list
        except (json_module.JSONDecodeError, IndexError, TypeError, ValueError):
            return None

    def _extract_from_regex(self, html: str) -> List[Anime]:
        """Extract anime info using regex patterns.

        Args:
            html: HTML content.

        Returns:
            List of Anime objects.
        """
        anime_list = []
        seen_ids = set()
        pattern = re.compile(PATTERNS["anime1_list"])

        for match in pattern.findall(html):
            detail_url, cat_id, title, episode = match
            if cat_id not in seen_ids:
                seen_ids.add(cat_id)
                anime_list.append(
                    Anime.create(
                        id=cat_id,
                        title=title.strip(),
                        detail_url=detail_url,
                        episode=int(episode),
                    )
                )

        return anime_list

    def parse_anime_detail(self, html: str) -> dict:
        """Parse anime detail page for additional info.

        Args:
            html: HTML content of the detail page.

        Returns:
            Dictionary with additional anime info.
        """
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        return {
            "year": self._extract_year(text),
            "season": self._extract_season(text),
            "subtitle_group": self._extract_subtitle_group(text),
        }

    def _extract_year(self, text: str) -> str:
        """Extract year from text.

        Args:
            text: Page text content.

        Returns:
            Year string or empty.
        """
        year_match = re.search(PATTERNS["year"], text)
        return year_match.group() if year_match else ""

    def _extract_season(self, text: str) -> str:
        """Extract season from text.

        Args:
            text: Page text content.

        Returns:
            Season string or empty.
        """
        for season in SEASONS:
            if season in text:
                return season
        return ""

    def _extract_subtitle_group(self, text: str) -> str:
        """Extract subtitle group from text.

        Args:
            text: Page text content.

        Returns:
            Subtitle group or empty.
        """
        for keyword in SUBTITLE_KEYWORDS:
            if keyword in text:
                return keyword
        return ""

    def parse_episode_list(self, detail_url: str) -> List[dict]:
        """Parse all episodes from an anime detail page.

        Args:
            detail_url: URL of the anime detail page.

        Returns:
            List of episode dictionaries with episode_num, title, url, date.
        """
        html = self.client.get(detail_url)
        return self._extract_episodes(html)

    def _extract_episodes(self, html: str) -> List[dict]:
        """Extract episode list from HTML.

        Args:
            html: HTML content of the detail page.

        Returns:
            List of episode dictionaries.
        """
        episodes = []
        soup = BeautifulSoup(html, "html.parser")

        # First, try to extract episodes from standard category listing format
        # Pattern: <h2 class="entry-title"><a href="https://anime1.me/27788">Princession Orchestra [37]</a></h2>
        title_links = soup.select('h2.entry-title a[href*="/"]')

        for link in title_links:
            href = link.get("href", "")
            title_text = link.get_text(strip=True)

            # Skip if this is just a category link
            if '/?cat=' in href or '/category/' in href:
                continue

            # Extract episode ID from URL like https://anime1.me/27788
            match = re.search(r'/(\d+)$', href)
            if not match:
                continue
            episode_id = match.group(1)

            # Extract episode number from title like "Princession Orchestra [37]"
            # Only accept numeric format [N], skip special formats like [劇場版], [SP], [OVA]
            # The actual episode number (e parameter) will be fetched from the episode page
            ep_match = re.search(r'\[(\d+(?:\.\d+)?)\]', title_text)
            if not ep_match:
                continue
            episode_num = ep_match.group(1)

            # Get clean title (remove episode number if present)
            title = re.sub(r'\s*\[\d+(?:\.\d+)?\]\s*$', '', title_text).strip()

            # Find the date in the same article
            article = link.find_parent('article')
            if article:
                time_elem = article.select_one('time.entry-date')
                if time_elem:
                    date = time_elem.get_text(strip=True)
                else:
                    date = ""
            else:
                date = ""

            episodes.append({
                "id": episode_id,
                "title": title,
                "episode": episode_num,
                "url": href,
                "date": date
            })

        # If no episodes found from listing, check if this is a single episode page
        # (like movie pages or standalone episodes)
        if not episodes:
            single_episode = self._extract_single_episode(soup)
            if single_episode:
                episodes.append(single_episode)

        return episodes

    def _extract_single_episode(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract episode info from a single episode/movie page.

        This handles pages that have a video player directly embedded,
        like https://anime1.me/27546 (劇場版『鏈鋸人 蕾潔篇』).

        Args:
            soup: BeautifulSoup object of the page.

        Returns:
            Episode dictionary or None if not a single episode page.
        """
        # Check if this is a single post page (has article with post class)
        article = soup.find('article')
        if not article:
            return None

        article_classes = article.get('class', [])
        if not any('post' in cls for cls in article_classes):
            return None

        # Try to get episode info from video tag
        video = soup.find('video')
        if not video:
            return None

        # Extract video data attributes
        api_req = video.get('data-apireq', '')
        vid = video.get('data-vid', '')
        video_id = vid or (re.search(r'"v":"([^"]+)"', api_req).group(1) if api_req else '')

        # Extract episode number from category ID in api_req or page
        episode_num = "1"  # Default for single episode
        cat_match = re.search(r'"c":"?(\d+)"?', api_req)
        if cat_match:
            category_id = cat_match.group(1)
            # For single episodes, the episode number might be in the API request
            ep_match = re.search(r'"e":"?(\d+)"?', api_req)
            if ep_match:
                episode_num = ep_match.group(1)

        # Extract title from entry-title
        title_elem = soup.find('h2', class_='entry-title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove episode number from title if present (only numeric format)
            title = re.sub(r'\s*\[\d+(?:\.\d+)?\]\s*$', '', title_text).strip()
        else:
            title = soup.title.string if soup.title else "Unknown"

        # Extract date
        time_elem = soup.select_one('time.entry-date')
        date = time_elem.get_text(strip=True) if time_elem else ""

        # Extract episode ID from article class (e.g., "post-27546")
        episode_id = ""
        for cls in article_classes:
            match = re.match(r'post-(\d+)', cls)
            if match:
                episode_id = match.group(1)
                break

        # If no episode ID from class, try to get from canonical
        if not episode_id:
            canonical = soup.find('link', rel='canonical')
            if canonical:
                url = canonical.get('href', '')
                match = re.search(r'/(\d+)$', url)
                if match:
                    episode_id = match.group(1)

        # Construct URL from episode ID
        url = f"{self._base_url}/{episode_id}" if episode_id else ""

        if not episode_id:
            return None

        return {
            "id": episode_id,
            "title": title,
            "episode": episode_num,
            "url": url,
            "date": date
        }

    def get_total_episode_pages(self, html: str) -> int:
        """Get total number of episode pages.

        Args:
            html: HTML content of the detail page.

        Returns:
            Total number of pages.
        """
        soup = BeautifulSoup(html, "html.parser")
        # Pattern: /page/2 or ?page=2
        page_links = soup.select('a[href*="/page/"]')

        max_page = 1
        for link in page_links:
            href = link.get("href", "")
            match = re.search(r'/page/(\d+)', href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)

        return max_page

    def get_total_pages(self, html: str) -> int:
        """Get total number of pages from HTML.

        Args:
            html: HTML content of the main page.

        Returns:
            Total number of pages.
        """
        soup = BeautifulSoup(html, "html.parser")
        page_links = soup.select('a[href*="category/"]')

        max_page = DEFAULTS["page"]
        for link in page_links:
            href = link.get("href", "")
            match = re.search(PATTERNS["page_number"], href)
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)

        return max_page

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
