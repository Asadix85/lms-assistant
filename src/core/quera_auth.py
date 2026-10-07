"""مدیریت احراز هویت Quera — با API داخلی."""

from loguru import logger

from src.core.exceptions import AuthenticationError
from src.core.quera_client import QueraHttpClient


class QueraAuth:
    """ورود/خروج به Quera (با API داخلی)."""

    LOGIN_API = "/accounts/api/login/"
    VERIFY_API = "/accounts/api/login/verify"
    LOGOUT_API = "/accounts/api/logout/"

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

    def _get_csrf_token(self) -> str | None:
        """گرفتن CSRF از cookie."""
        # اول صفحه login رو بگیر تا cookie ست بشه
        self.client.get("/accounts/login")
        return self.client.cookies.get("csrf_token")

    def login(self, identifier: str, password: str) -> bool:
        """ورود به Quera.

        Args:
            identifier: ایمیل یا شماره موبایل
            password: رمز عبور

        Returns:
            True اگر موفق
        """
        logger.info(f"شروع ورود به Quera برای: {identifier}")

        try:
            # === قدم ۰: گرفتن CSRF از cookie ===
            logger.debug("قدم ۰: GET /accounts/login برای CSRF")
            r0 = self.client.get("/accounts/login")
            csrf_token = self.client.cookies.get("csrf_token")

            if not csrf_token:
                logger.error("CSRF token (cookie csrf_token) پیدا نشد!")
                return False

            logger.debug(f"✅ CSRF: {csrf_token[:20]}...")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-CSRFToken": csrf_token,
                "Origin": self.client.BASE_URL,
                "Referer": f"{self.client.BASE_URL}/accounts/login",
            }

            # === قدم ۱: POST /accounts/api/login/ ===
            logger.debug("قدم ۱: POST /accounts/api/login/")
            r1 = self.client.post(
                self.LOGIN_API,
                json={
                    "identifier": identifier,
                    "captcha_token": "",
                    "preferred_process": "password",
                },
                headers=headers,
            )

            logger.debug(f"پاسخ قدم ۱: {r1.status_code}")

            try:
                data1 = r1.json()
            except Exception:
                logger.error(f"پاسخ JSON نبود: {r1.text[:200]}")
                return False

            logger.debug(f"پاسخ: {data1}")

            # بررسی next_step
            next_step = data1.get("next_step")
            if next_step != "password":
                logger.error(f"next_step غیرمنتظره: {next_step}")
                return False

            # === قدم ۲: POST /accounts/api/login/verify ===
            logger.debug("قدم ۲: POST /accounts/api/login/verify")
            r2 = self.client.post(
                self.VERIFY_API,
                json={
                    "identifier": identifier,
                    "step": "password",
                    "credential": password,
                    "captcha_token": "",
                },
                headers=headers,
            )

            logger.debug(f"پاسخ قدم ۲: {r2.status_code}")

            try:
                data2 = r2.json()
            except Exception:
                logger.error(f"پاسخ JSON نبود: {r2.text[:200]}")
                return False

            logger.debug(f"پاسخ: {data2}")

            # === بررسی موفقیت ===
            if r2.status_code == 200 and "redirect_url" in data2:
                # چک session_id
                session_id = self.client.cookies.get("session_id")
                if not session_id:
                    logger.warning("session_id cookie ست نشد")
                    return False

                self._authenticated = True
                self._identifier = identifier
                logger.info(
                    f"✅ ورود موفق! redirect: {data2.get('redirect_url')}"
                )
                return True

            # اگه خطا داشت
            error = data2.get("error") or data2.get("detail") or str(data2)
            logger.warning(f"❌ ورود ناموفق: {error}")
            self._authenticated = False
            return False

        except Exception as e:
            logger.error(f"خطا در ورود به Quera: {e}")
            import traceback
            traceback.print_exc()
            raise AuthenticationError(f"خطا در ورود: {e}") from e

    def logout(self) -> None:
        """خروج از Quera."""
        if not self._authenticated:
            return
        try:
            csrf = self.client.cookies.get("csrf_token")
            self.client.post(
                self.LOGOUT_API,
                headers={
                    "X-CSRFToken": csrf,
                    "Content-Type": "application/json",
                },
            )
            self._authenticated = False
            self._identifier = None
            logger.info("✅ خروج از Quera")
        except Exception as e:
            logger.warning(f"خطا در خروج: {e}")

    def verify(self) -> bool:
        """تست معتبر بودن session."""
        try:
            r = self.client.get("/dashboard")
            return "/accounts/login" not in str(r.url)
        except Exception:
            return False