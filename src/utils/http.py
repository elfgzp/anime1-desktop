"""HTTP request utilities."""
import logging
import subprocess
import sys
import time
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import SSLError as Urllib3SSLError

from ..config import (
    HEADERS,
    MAX_RETRIES,
    RETRY_BACKOFF,
    RETRY_STATUS_CODES,
    DEFAULT_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Domains with SSL issues that need special handling
SSL_TRUSTED_DOMAINS = {'anime1.pw'}

# Domains that require curl (more tolerant SSL handling)
CURL_ONLY_DOMAINS = {'anime1.pw'}


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


def fetch_page_with_curl(url: str, timeout: int = 30) -> str:
    """Fetch a web page using curl (for domains with SSL issues).

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        The HTML content of the page.

    Raises:
        requests.RequestException: If the request fails.
    """
    # 自动追踪 curl 请求
    from .trace import TraceSpan, is_tracing_enabled

    if is_tracing_enabled():
        from urllib.parse import urlparse
        parsed = urlparse(url)
        trace_name = f"curl:{parsed.netloc}{parsed.path}"
        span = TraceSpan(trace_name, 'external_api', {'url': url, 'method': 'CURL'})
    else:
        span = None

    try:
        result = _curl_impl(url, timeout)
        if span:
            span.end(success=True)
        return result
    except Exception as e:
        if span:
            span.end(success=False, error=str(e))
        raise


def _curl_impl(url: str, timeout: int = 30) -> str:
    curl_commands = [
        # Approach 1: Standard curl with modern TLS
        [
            'curl', '-s', '-L', '--max-time', str(timeout),
            '--connect-timeout', '10',
            '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept-Language: zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            url
        ],
        # Approach 2: Allow insecure (don't verify SSL)
        [
            'curl', '-k', '-s', '-L', '--max-time', str(timeout),
            '--connect-timeout', '10',
            '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            url
        ],
        # Approach 3: Try legacy TLS versions
        [
            'curl', '-s', '-L', '--max-time', str(timeout),
            '--connect-timeout', '10',
            '--tlsv1.0', '--tlsv1.1',
            '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ],
    ]

    for i, cmd in enumerate(curl_commands):
        try:
            # On Windows, use CREATE_NO_WINDOW to avoid terminal flash
            run_kwargs = {
                'capture_output': True,
                'text': True,
                'timeout': timeout + 5,
            }
            if sys.platform == "win32":
                run_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(cmd, **run_kwargs)
            if result.returncode == 0 and result.text.strip():
                return result.text
            logger.debug(f"Curl approach {i+1} failed for {url}: returncode={result.returncode}")
        except subprocess.TimeoutExpired:
            logger.debug(f"Curl approach {i+1} timed out for {url}")
        except Exception as e:
            logger.debug(f"Curl approach {i+1} error for {url}: {e}")

    raise requests.RequestException(f"All curl approaches failed for {url}")


def fetch_page(
    url: str,
    session: Optional[requests.Session] = None,
    delay: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
    ignore_ssl: bool = False,
) -> str:
    """Fetch a web page and return its content.

    Args:
        url: The URL to fetch.
        session: Optional requests session to use.
        delay: Delay in seconds before fetching (for rate limiting).
        timeout: Request timeout in seconds.
        ignore_ssl: Whether to ignore SSL errors for this request.

    Returns:
        The HTML content of the page.

    Raises:
        requests.RequestException: If the request fails.
    """
    # 自动追踪所有 HTTP 请求
    from .trace import TraceSpan, is_tracing_enabled

    if is_tracing_enabled():
        # 从 URL 提取域名作为追踪名称
        from urllib.parse import urlparse
        parsed = urlparse(url)
        trace_name = f"http_get:{parsed.netloc}{parsed.path}"
        span = TraceSpan(trace_name, 'external_api', {'url': url, 'method': 'GET'})
    else:
        span = None

    try:
        result = _fetch_page_impl(url, session, delay, timeout, ignore_ssl)
        if span:
            span.end(success=True)
        return result
    except Exception as e:
        if span:
            span.end(success=False, error=str(e))
        raise


def _fetch_page_impl(
    url: str,
    session: Optional[requests.Session] = None,
    delay: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
    ignore_ssl: bool = False,
) -> str:
    """Internal implementation of fetch_page."""
    if delay > 0:
        time.sleep(delay)

    # Check if we need special handling for this domain
    needs_ssl_trust = any(domain in url for domain in SSL_TRUSTED_DOMAINS)

    # For domains with known SSL issues, use curl
    if needs_ssl_trust:
        try:
            return fetch_page_with_curl(url, timeout)
        except requests.RequestException as e:
            logger.warning(f"curl failed for {url}: {e}, trying requests with verify=False...")
            # Fall back to requests with verify=False
            pass

    if session is None:
        session = create_session()

    try:
        if ignore_ssl or needs_ssl_trust:
            # For domains with SSL issues, use a session that doesn't verify
            response = session.get(url, timeout=timeout, verify=False)
        else:
            response = session.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.SSLError as e:
        if needs_ssl_trust and not ignore_ssl:
            # Retry with SSL verification disabled for known problematic domains
            logger.warning(f"SSL error for {url}, retrying without verification...")
            response = session.get(url, timeout=timeout, verify=False)
            response.raise_for_status()
        else:
            raise

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
