"""Text conversion utilities for anime search."""
from typing import List
from hanziconv import HanziConv


def to_traditional(keyword: str) -> str:
    """Convert simplified Chinese to traditional Chinese."""
    return HanziConv.toTraditional(keyword)


def to_simplified(keyword: str) -> str:
    """Convert traditional Chinese to simplified Chinese."""
    return HanziConv.toSimplified(keyword)


def get_search_variants(keyword: str) -> List[str]:
    """Get all search variants for a keyword.

    Uses hanziconv for simplified/traditional conversion.

    Args:
        keyword: Search keyword (usually in Simplified Chinese)

    Returns:
        List of search variants including simplified, traditional forms
    """
    variants = set()
    keyword_str = str(keyword) if not isinstance(keyword, str) else keyword

    # Add original keyword
    variants.add(keyword_str)

    # Add simplified/traditional variants using hanziconv
    try:
        variants.add(to_traditional(keyword_str))
        variants.add(to_simplified(keyword_str))
    except Exception:
        pass

    # Remove empty strings and non-strings
    variants = [v for v in variants if v and isinstance(v, str) and len(v.strip()) > 0]
    return list(variants)
