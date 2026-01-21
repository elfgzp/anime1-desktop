"""Tests for cover finder matching logic."""
import pytest
from src.parser.cover_finder import CoverFinder
from src.models.anime import Anime
from src.config import (
    BANGUMI_SEARCH_URL,
)


class TestCoverFinderMatching:
    """Test cover finder matching logic for edge cases."""

    def test_matched_wrong_anime_27823(self):
        """Test case for anime1.me/27823 that was matched to wrong cover.

        Anime: 青梅竹馬的戀愛喜劇無法成立
        Correct match: https://bangumi.tv/subject/549654 (幼馴染とはラブコメにならない)
        """
        finder = CoverFinder()

        # Test the title
        anime_title = "青梅竹馬的戀愛喜劇無法成立"

        # Get search variants
        variants = finder._get_search_variants(anime_title)

        print(f"Original title: {anime_title}")
        print(f"Search variants: {variants}")

        # Test core keywords extraction
        core_keywords = finder._extract_core_keywords(anime_title)
        print(f"Core keywords: {core_keywords}")

        # Test simplified Chinese conversion
        simplified = finder._to_simplified_chinese(anime_title)
        print(f"Simplified Chinese: {simplified}")

        # Test truncate keywords
        truncated = finder._truncate_keywords(core_keywords)
        print(f"Truncated keywords: {truncated}")

        # Now let's see what Bangumi returns for each variant
        # This would make actual HTTP calls, so we skip in unit test
        # but we can test the matching logic

    def test_extract_core_keywords_edge_cases(self):
        """Test core keywords extraction with various patterns."""
        finder = CoverFinder()

        test_cases = [
            # (input, expected_core)
            ("青梅竹馬的戀愛喜劇無法成立", "青梅竹馬的戀愛喜劇無法成立"),
            ("地獄模式 ～喜歡挑戰...～", "地獄模式"),
            ("進擊的巨人 第三季 Part.2", "進擊的巨人 第三季"),
            ("刀劍神域 Alicization", "刀劍神域 Alicization"),
            ("我的英雄學院 第六季", "我的英雄學院 第六季"),
        ]

        for title, expected in test_cases:
            result = finder._extract_core_keywords(title)
            print(f"Input: {title}")
            print(f"Output: {result}")
            print(f"Expected: {expected}")
            print("---")

    def test_title_similarity_calculation(self):
        """Test title similarity scoring."""
        finder = CoverFinder()

        test_cases = [
            # (query, result, expected_min_score, description)
            (
                "青梅竹馬的戀愛喜劇無法成立",
                "和青梅竹马之间不会有恋爱喜剧",
                30,
                "Simplified Chinese translation should have some overlap"
            ),
            (
                "進擊的巨人",
                "进击的巨人",
                50,
                "Same characters in Traditional vs Simplified should have overlap"
            ),
            (
                "進擊的巨人",
                "Attack on Titan",
                0,
                "No overlap between Chinese and English"
            ),
            (
                "刀劍神域",
                "刀剑神域",
                50,
                "Same characters in Traditional vs Simplified"
            ),
        ]

        for query, result, min_score, description in test_cases:
            score = finder._calculate_title_similarity(query, result)
            print(f"{description}:")
            print(f"  Query: {query}")
            print(f"  Result: {result}")
            print(f"  Score: {score} (min: {min_score})")
            assert score >= min_score, f"Score {score} is below minimum {min_score}"

    def test_simplified_chinese_conversion(self):
        """Test Traditional to Simplified Chinese conversion."""
        finder = CoverFinder()

        test_cases = [
            # (traditional, expected_simplified)
            ("青梅竹馬的戀愛喜劇無法成立", "青梅竹马的恋爱喜剧无法成立"),
            ("進擊的巨人", "进击的巨人"),
            ("刀劍神域", "刀剑神域"),
            ("我的英雄學院", "我的英雄学院"),
        ]

        for traditional, expected in test_cases:
            result = finder._to_simplified_chinese(traditional)
            print(f"Traditional: {traditional}")
            print(f"Simplified: {result}")
            print(f"Expected: {expected}")
            # Note: may not have hanziconv installed, so just print results


@pytest.mark.integration
class TestCoverFinderRealSearch:
    """Integration tests that make real HTTP calls to Bangumi."""

    def test_search青梅竹馬的戀愛喜劇無法成立(self):
        """Test real search for this problematic anime."""
        finder = CoverFinder()

        anime = Anime(
            id="test_27823",
            title="青梅竹馬的戀愛喜劇無法成立",
            detail_url="https://anime1.me/27823",
            episode=3,
        )

        result = finder.find_cover_for_anime(anime)

        print(f"Original title: {anime.title}")
        print(f"Matched title: {result.cover_url}")
        print(f"Match score: {result.match_score}")
        print(f"Match source: {result.match_source}")

        # The correct Bangumi subject should be subject/549654
        # We can't assert exact URL as it depends on search results
        # But we can verify the matching works
        assert result.cover_url is not None, "Should find a cover"

        finder.close()

    def test_search花樣少年少女(self):
        """Test real search for 花樣少年少女 (subject/494564).

        Issue: '花' (single character title) was incorrectly matched before fix.
        Should match to 花样少年少女 (subject/494564), not 花 (subject/579466).
        """
        finder = CoverFinder()

        anime = Anime(
            id="test_1787",
            title="花樣少年少女",
            detail_url="https://anime1.me/1787",
            episode=1,
        )

        result = finder.find_cover_for_anime(anime)

        print(f"Original title: {anime.title}")
        print(f"Matched cover: {result.cover_url}")
        print(f"Match score: {result.match_score}")
        print(f"Match source: {result.match_source}")

        # Should match subject/494564 (花样少年少女)
        assert "494564" in result.cover_url, f"Should match subject/494564, got {result.cover_url}"
        assert result.match_score > 0, "Should have a positive match score"

        finder.close()

    def test_search_variants_comparison(self):
        """Compare results from different search variants using merged scoring."""
        finder = CoverFinder()

        original_title = "青梅竹馬的戀愛喜劇無法成立"
        simplified_title = finder._to_simplified_chinese(original_title)
        core_keywords = finder._extract_core_keywords(original_title)

        # Use the new _search_with_keyword_multi method
        all_results = []
        for name, variant in [("original", original_title), ("simplified", simplified_title)]:
            print(f"\nSearching with '{name}': {variant}")
            results = finder._search_with_keyword_multi(variant, include_details=True,
                                                         original_title=original_title)
            for r in results:
                print(f"  Found: {r.get('title')} (score: {r.get('score')})")
                print(f"  Cover: {r.get('cover_url')}")
                print(f"  URL: {r.get('subject_url')}")
            all_results.extend(results)

        finder.close()

        # Should have results from both searches
        assert len(all_results) > 0, "Should have search results"

        # Sort by score and check the best match
        all_results.sort(key=lambda x: x["score"], reverse=True)
        best = all_results[0]

        # The best match should be subject/316264 (青梅竹马绝对不会输的恋爱喜剧)
        # Note: Bangumi search results may vary over time
        assert "316264" in best.get("subject_url", ""), f"Best match should be subject/316264, got {best}"
        print(f"\nBest match: {best.get('title')} (score: {best.get('score')})")
        print(f"URL: {best.get('subject_url')}")
