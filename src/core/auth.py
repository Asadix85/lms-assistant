"""مدیریت احراز هویت LMS."""

import re

from loguru import logger

from src.core.exceptions import AuthenticationError
from src.core.http_client import LMSHttpClient
from config.constants import LOGIN_PATH, LOGOUT_PATH


# الگوی User ID در URL: /pages/nodemain/?r=1072797
USER_ID_PATTERN = re.compile(r"[?&]r=(\d+)")


class LMSAuth:
    """مدیریت ورود/خروج به LMS.

    این کلاس روی LMSHttpClient کار می‌کند و session را مدیریت می‌کند.
    """

    def __init__(self, client: LMSHttpClient) -> None:
        self.client = client
        self._authenticated = False
        self._user_id: str | None = None

    # === Properties ===

    @property
    def is_authenticated(self) -> bool:
        """آیا وارد شده‌ایم؟"""
        return self._authenticated

    @property
    def user_id(self) -> str | None:
        """شناسه کاربر (اگر وارد شده)."""
        return self._user_id

    # === Login ===

    def login(self, username: str, password: str) -> bool:
        """ورود به LMS.

        Args:
            username: شماره دانشجویی
            password: رمز عبور

        Returns:
            True اگر موفق، False اگر ناموفق

        Raises:
            AuthenticationError: اگر خطای غیرمنتظره رخ داد
        """
        logger.info(f"شروع ورود به LMS برای کاربر: {username}")

        try:
            # قدم ۱: GET صفحه اصلی برای دریافت cookie اولیه
            logger.debug("قدم ۱: GET / برای گرفتن cookie اولیه")
            self.client.get("/")

            # قدم ۲: POST فرم لاگین
            logger.debug("قدم ۲: POST /login")
            response = self.client.post(
                LOGIN_PATH,
                data={
                    "username": username,
                    "password": password,
                    "submit": "ورود",
                    "remember": "1",
                    "return_url": "",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": str(self.client.base_url) + "/",
                    "Origin": str(self.client.base_url),
                },
            )

            # قدم ۳: بررسی نتیجه
            logger.debug(f"پاسخ لاگین: {response.status_code}")
            logger.debug(f"URL نهایی: {response.url}")

            # اگر به nodemain ریدایرکت شد → موفق
            if "/pages/nodemain" in str(response.url):
                self._authenticated = True

                # استخراج user_id از URL
                match = USER_ID_PATTERN.search(str(response.url))
                if match:
                    self._user_id = match.group(1)
                    logger.info(f"✅ ورود موفق. User ID: {self._user_id}")
                else:
                    logger.info("✅ ورود موفق (user_id پیدا نشد)")

                return True

            # اگر در صفحه لاگین ماندیم → ناموفق
            logger.warning("❌ ورود ناموفق - در صفحه لاگین ماندیم")
            self._authenticated = False
            self._user_id = None
            return False

        except Exception as e:
            logger.error(f"خطا در ورود: {e}")
            raise AuthenticationError(f"خطا در ورود: {e}") from e

    # === Logout ===

    def logout(self) -> None:
        """خروج از LMS."""
        if not self._authenticated:
            logger.debug("قبلاً خارج شده‌ایم")
            return

        try:
            logger.info("خروج از LMS...")
            self.client.get(LOGOUT_PATH)
            self._authenticated = False
            self._user_id = None
            logger.info("✅ خروج موفق")
        except Exception as e:
            logger.warning(f"خطا در خروج: {e}")

    # === Test Authentication ===

    def verify(self) -> bool:
        """تست اینکه session هنوز معتبر است."""
        try:
            response = self.client.get("/pages/nodemain")
            is_valid = "/pages/nodemain" in str(response.url)
            logger.debug(f"verify: {is_valid}")
            return is_valid
        except Exception as e:
            logger.warning(f"خطا در verify: {e}")
            return False

    def __repr__(self) -> str:
        status = "authenticated" if self._authenticated else "not authenticated"
        return f"LMSAuth({status}, user_id={self._user_id!r})"