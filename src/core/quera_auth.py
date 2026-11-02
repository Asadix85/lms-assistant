"""مدیریت احراز هویت Quera — با استفاده از کوکی مرورگر (دور زدن کپچا)."""

from pathlib import Path
from loguru import logger

from src.core.exceptions import AuthenticationError
from src.core.quera_client import QueraHttpClient


class QueraAuth:
    """ورود/خروج به Quera با استفاده از کوکی آماده."""

    def __init__(self, client: QueraHttpClient) -> None:
        self.client = client
        self._authenticated = False
        self._identifier: str | None = None
        self.cookie_file = Path("quera_cookie.txt")

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    @property
    def identifier(self) -> str | None:
        return self._identifier

    def login(self, identifier: str, password: str) -> bool:
        """
        به جای لاگین با رمز، کوکی ذخیره‌شده از مرورگر را بارگذاری می‌کند.
        (رمز عبور نادیده گرفته می‌شود)
        """
        logger.info("در حال بارگذاری کوکی از فایل quera_cookie.txt...")

        if not self.cookie_file.exists():
            logger.error("فایل quera_cookie.txt پیدا نشد! لطفاً یک بار دستی در مرورگر لاگین کنید و کوکی را در این فایل ذخیره کنید.")
            return False

        try:
            cookie_value = self.cookie_file.read_text().strip()
            if not cookie_value:
                logger.error("فایل کوکی خالی است.")
                return False

            # تنظیم کوکی در کلاینت httpx
            # دامنه را quera.org تنظیم می‌کنیم
            self.client._client.cookies.set("sessionid", cookie_value, domain="quera.org")

            # تست اینکه آیا کوکی معتبر است یا خیر
            test_resp = self.client.get("/dashboard")
            if "/accounts/login" in str(test_resp.url):
                logger.error("کوکی منقضی شده است. لطفاً دوباره از مرورگر کوکی جدید بگیرید.")
                return False

            self._authenticated = True
            self._identifier = identifier
            logger.success("✅ کوکی معتبر است. ورود به کوئرا انجام شد.")
            return True

        except Exception as e:
            logger.error(f"خطا در خواندن یا تنظیم کوکی: {e}")
            return False

    def logout(self) -> None:
        self._authenticated = False
        self._identifier = None

    def verify(self) -> bool:
        if not self.cookie_file.exists():
            return False
        try:
            cookie_value = self.cookie_file.read_text().strip()
            self.client._client.cookies.set("sessionid", cookie_value, domain="quera.org")
            r = self.client.get("/dashboard")
            return "/accounts/login" not in str(r.url)
        except Exception:
            return False