"""مدیریت احراز هویت Quera — کوکی‌محور (دور زدن کپچا)."""
import re
from loguru import logger
from src.core.exceptions import AuthenticationError
from src.core.quera_client import QueraHttpClient


class QueraAuth:
    """ورود به Quera با کوکی نشست (sessionid) یا username/password."""

    CSRF_PATTERN = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')

    def __init__(self, client: QueraHttpClient) -> None:
        self.client = client
        self._authenticated = False
        self._identifier: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    @property
    def identifier(self) -> str | None:
        return self._identifier

    def login_with_cookie(self, cookie_value: str) -> bool:
        """
        ورود با کوکی نشست کوئرا.
        
        Args:
            cookie_value: مقدار کوکی 'sessionid' از مرورگر
            
        Returns:
            True اگر کوکی معتبر باشد
        """
        if not cookie_value or not cookie_value.strip():
            logger.error("کوکی کوئرا خالی است")
            return False

        cookie_value = cookie_value.strip()
        
        # حذف پیشوند احتمالی
        if "=" in cookie_value:
            parts = cookie_value.split("=", 1)
            if parts[0].strip().lower() == "sessionid":
                cookie_value = parts[1].strip()

        try:
            self.client._client.cookies.set(
                "sessionid", cookie_value, domain="quera.org"
            )

            test_resp = self.client.get("/dashboard")
            
            if "/accounts/login" in str(test_resp.url):
                logger.error("کوکی کوئرا منقضی شده یا نامعتبر است")
                return False

            self._authenticated = True
            self._identifier = "cookie_auth"
            logger.success("✅ ورود به کوئرا با کوکی موفق بود")
            return True

        except Exception as e:
            logger.error(f"خطا در ورود با کوکی: {e}")
            return False

    def login(self, identifier: str, password: str) -> bool:
        """
        تلاش برای ورود با username/password.
        اگر 403 بگیریم، یعنی کپچا دارد و باید از کوکی استفاده شود.
        """
        if not identifier or not password:
            logger.error("نام کاربری یا رمز عبور کوئرا خالی است")
            return False

        try:
            logger.info(f"شروع ورود به Quera برای کاربر: {identifier}")
            
            # قدم ۱: GET صفحه لاگین برای CSRF token
            logger.debug("قدم ۱: GET /accounts/login")
            login_page = self.client.get("/accounts/login")
            
            csrf_token = None
            csrf_match = self.CSRF_PATTERN.search(login_page.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                logger.debug(f"CSRF token یافت شد: {csrf_token[:8]}...")
            
            # قدم ۲: POST فرم لاگین
            logger.debug("قدم ۲: POST /accounts/login")
            login_data = {
                "login": identifier,
                "password": password,
            }
            if csrf_token:
                login_data["csrfmiddlewaretoken"] = csrf_token
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://quera.org/accounts/login/",
                "Origin": "https://quera.org",
            }
            
            try:
                response = self.client.post(
                    "/accounts/login/",
                    data=login_data,
                    headers=headers,
                )
            except Exception as e:
                error_str = str(e)
                if "403" in error_str or "Forbidden" in error_str:
                    logger.error("❌ خطای 403: کوئرا کپچا دارد. لطفاً از کوکی مرورگر استفاده کنید.")
                    return False
                raise
            
            logger.debug(f"پاسخ لاگین: {response.status_code}")
            logger.debug(f"URL نهایی: {response.url}")
            
            # اگر به dashboard یا course ریدایرکت شد → موفق
            if "/dashboard" in str(response.url) or "/course" in str(response.url):
                self._authenticated = True
                self._identifier = identifier
                logger.success(f"✅ ورود موفق به Quera برای کاربر: {identifier}")
                return True
            
            # اگر در صفحه لاگین ماندیم → ناموفق
            if "/accounts/login" in str(response.url):
                logger.warning("❌ ورود ناموفق - در صفحه لاگین ماندیم")
                return False
            
            logger.warning(f"وضعیت نامشخص بعد از لاگین: {response.url}")
            return False
            
        except Exception as e:
            logger.error(f"خطا در ورود به Quera: {e}")
            return False

    def verify(self) -> bool:
        """تست اینکه نشست هنوز معتبر است."""
        if not self._authenticated:
            return False
        try:
            response = self.client.get("/dashboard")
            return "/accounts/login" not in str(response.url)
        except Exception as e:
            logger.warning(f"خطا در verify: {e}")
            return False

    def logout(self) -> None:
        self._authenticated = False
        self._identifier = None