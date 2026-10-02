"""HTTP client برای LMS با session management."""

import time
from typing import Any

import httpx
from loguru import logger

from config.constants import DEFAULT_USER_AGENT
from src.core.exceptions import ConnectionError


class LMSHttpClient:
    """HTTP client برای LMS.

    این کلاس یک wrapper روی httpx.Client است که:
    - Session (cookies) را مدیریت می‌کند
    - Retry logic دارد
    - Timeout دارد
    - Logging می‌کند
    """

    def __init__(
            self,
            base_url: str,
            timeout: int = 30,
            max_retries: int = 3,
            user_agent: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Headers پیش‌فرض
        self._headers = {
            "User-Agent": user_agent or DEFAULT_USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # ساخت httpx.Client
        # ⚠️ trust_env=False → Proxy سیستمی را نادیده بگیر
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers,
            follow_redirects=True,
            trust_env=False,  # ← حیاتی!
        )

        logger.info(f"LMSHttpClient ساخته شد: {self.base_url}")

        # ساخت httpx.Client
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers,
            follow_redirects=True,
        )

        logger.info(f"LMSHttpClient ساخته شد: {self.base_url}")

    # === Properties ===

    @property
    def cookies(self) -> httpx.Cookies:
        """دسترسی به کوکی‌ها."""
        return self._client.cookies

    @property
    def is_closed(self) -> bool:
        """آیا client بسته است؟"""
        return self._client.is_closed

    # === HTTP Methods ===

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """GET request با retry."""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """POST request با retry."""
        return self._request("POST", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """درخواست داخلی با retry logic."""
        last_exception: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"{method} {path} (تلاش {attempt}/{self.max_retries})")
                response = self._client.request(method, path, **kwargs)
                logger.debug(f"  → {response.status_code} ({len(response.content)} bytes)")
                return response

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"  → Timeout (تلاش {attempt})")

            except httpx.NetworkError as e:
                last_exception = e
                logger.warning(f"  → Network error: {e} (تلاش {attempt})")

            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(f"  → HTTP error: {e} (تلاش {attempt})")

            # صبر قبل از تلاش بعدی (exponential backoff)
            if attempt < self.max_retries:
                wait = 2 ** (attempt - 1)
                logger.debug(f"  → صبر {wait} ثانیه...")
                time.sleep(wait)

        # همه تلاش‌ها شکست خورد
        raise ConnectionError(
            f"درخواست {method} {path} بعد از {self.max_retries} تلاش شکست خورد"
        ) from last_exception

    # === Lifecycle ===

    def close(self) -> None:
        """بستن client."""
        if not self._client.is_closed:
            self._client.close()
            logger.info("LMSHttpClient بسته شد")

    def __enter__(self) -> "LMSHttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"LMSHttpClient(base_url={self.base_url!r}, closed={self.is_closed})"