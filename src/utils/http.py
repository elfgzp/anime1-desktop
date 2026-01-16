"""HTTP request utilities."""
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import (
    HEADERS,
    MAX_RETRIES,
    RETRY_BACKOFF,
    RETRY_STATUS_CODES,
    DEFAULT_TIMEOUT,
)


def create_session() -> requests.Session:
    """Create a requests session with retry logic.

    Returns:
        Configured requests Session object.
    """
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=RETRY_STATUS_CODES,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


def fetch_page(
    url: str,
    session: Optional[requests.Session] = None,
    delay: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Fetch a web page and return its content.

    Args:
        url: The URL to fetch.
        session: Optional requests session to use.
        delay: Delay in seconds before fetching (for rate limiting).
        timeout: Request timeout in seconds.

    Returns:
        The HTML content of the page.
    """
    if delay > 0:
        time.sleep(delay)

    if session is None:
        session = create_session()

    response = session.get(url, timeout=timeout)
    response.raise_for_status()

    # Force UTF-8 encoding to handle Chinese characters properly
    response.encoding = 'utf-8'
    return response.text


class HttpClient:
    """HTTP client with built-in session management and rate limiting."""

    def __init__(
        self,
        delay: float = 0.3,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """Initialize the HTTP client.

        Args:
            delay: Delay between requests in seconds.
            timeout: Request timeout in seconds.
        """
        self.delay = delay
        self.timeout = timeout
        self.session = create_session()

    def get(self, url: str) -> str:
        """GET request with rate limiting.

        Args:
            url: The URL to fetch.

        Returns:
            The HTML content of the page.
        """
        return fetch_page(url, self.session, self.delay, self.timeout)

    def get_with_timeout(self, url: str, timeout: int) -> str:
        """GET request with custom timeout.

        Args:
            url: The URL to fetch.
            timeout: Request timeout in seconds.

        Returns:
            The HTML content of the page.
        """
        return fetch_page(url, self.session, self.delay, timeout)

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
