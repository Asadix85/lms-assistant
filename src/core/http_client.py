import time
from typing import Any, Callable

import httpx
from loguru import logger

# وضعیت‌های HTTP که تلاش مجدد معنادار هستند
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class LMSHttpClient:
    def __init__(
            self,
            base_url: str,
            timeout: float = 30.0,
            max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

        # 👇 این متغیر برای «لاگین خودکار در پس‌زمینه» استفاده می‌شود
        self.reauth_callback: Callable[[], bool] | None = None

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

    def _is_session_expired(self, response: httpx.Response) -> bool:
        """تشخیص اینکه آیا سامانه کوکی ما را منقضی کرده است یا خیر."""
        # بررسی خطاهای احراز هویت
        if response.status_code in (401, 403):
            return True

        # بررسی متن صفحاتی که در فایل‌های HTML فرستادید
        text = response.text
        if "لاگین شما منقضی شده است" in text or "برای ورود به جلسه آنلاین نیاز است" in text:
            return True

        return False

    def _request(
            self,
            method: str,
            url: str,
            **kwargs: Any,
    ) -> httpx.Response:
        is_retry_after_reauth = False  # جلوگیری از حلقه بی‌نهایت

        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, url, **kwargs)

                # 👇 بررسی انقضای نشست قبل از raise_for_status
                if self._is_session_expired(response):
                    if not is_retry_after_reauth and self.reauth_callback:
                        logger.warning(f"⚠️ نشست منقضی شده است ({url}). تلاش برای لاگین خودکار...")
                        success = self.reauth_callback()
                        if success:
                            is_retry_after_reauth = True
                            logger.info("✅ لاگین خودکار موفق. ارسال مجدد درخواست...")
                            # ارسال مجدد بدون sleep
                            response = self._client.request(method, url, **kwargs)
                            if not self._is_session_expired(response):
                                response.raise_for_status()
                                return response
                        else:
                            logger.error("❌ لاگین خودکار ناموفق بود.")
                    else:
                        logger.error("❌ لاگین خودکار قبلاً شکست خورده یا تعریف نشده است.")

                # بررسی خطاهای معمولی HTTP
                response.raise_for_status()
                return response

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt == self.max_retries - 1:
                    raise

                delay = 2 ** attempt
                logger.warning(
                    "HTTP request failed: {} {} | retry in {}s | {}",
                    method, url, delay, exc,
                )
                time.sleep(delay)

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in RETRYABLE_STATUS or attempt == self.max_retries - 1:
                    raise

                delay = 2 ** attempt
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        pass

                logger.warning(
                    "HTTP {} for {} {} | retry in {}s",
                    status, method, url, delay,
                )
                time.sleep(delay)

        raise RuntimeError("HTTP request failed")

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", url, **kwargs)

    @property
    def cookies(self):
        return self._client.cookies

    @property
    def is_closed(self) -> bool:
        """آیا کلاینت بسته شده است؟"""
        return self._client.is_closed

    def close(self):
        self._client.close()

    def __enter__(self) -> "LMSHttpClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()