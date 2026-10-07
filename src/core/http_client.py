from typing import Any

import httpx
from loguru import logger


class LMSHttpClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
        }

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers,
            follow_redirects=True,
            trust_env=False,
        )

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(
                    method,
                    url,
                    **kwargs,
                )

                response.raise_for_status()

                return response

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
            ) as exc:
                if attempt == self.max_retries - 1:
                    raise

                delay = 2**attempt

                logger.warning(
                    "HTTP request failed: {} {} | retry in {}s | {}",
                    method,
                    url,
                    delay,
                    exc,
                )

                import time
                time.sleep(delay)

        raise RuntimeError("HTTP request failed")

    def get(
        self,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._request(
            "GET",
            url,
            **kwargs,
        )

    def post(
        self,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        return self._request(
            "POST",
            url,
            **kwargs,
        )

    @property
    def cookies(self):
        return self._client.cookies

    def close(self):
        self._client.close()