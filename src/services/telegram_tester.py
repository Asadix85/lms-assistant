"""تست اتصال Telegram."""

import httpx
from loguru import logger

from config.settings import settings


class TelegramTester:
    """تست ارسال پیام به تلگرام."""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    @staticmethod
    def test_connection(chat_id: str) -> tuple[bool, str]:
        """ارسال پیام تستی به تلگرام.

        Args:
            chat_id: Chat ID کاربر

        Returns:
            (success, message)
        """
        token = settings.telegram_bot_token
        if not token:
            return False, "Bot Token توی .env تنظیم نشده"

        if not chat_id:
            return False, "Chat ID خالیه"

        # پیام تستی
        text = (
            "🧪 <b>تست اتصال LMS Assistant</b>\n\n"
            "✅ اتصال با موفقیت برقرار شد!\n\n"
            "از این به بعد، نوتیفیکیشن‌های LMS Assistant\n"
            "به این چت ارسال می‌شه."
        )

        url = TelegramTester.API_URL.format(token=token)

        try:
            r = httpx.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=15,
            )

            if r.status_code == 200:
                data = r.json()
                if data.get("ok"):
                    logger.info(f"✅ تست تلگرام موفق: {chat_id}")
                    return True, "پیام تستی ارسال شد!"
                else:
                    error = data.get("description", "خطای نامشخص")
                    logger.warning(f"❌ تست تلگرام ناموفق: {error}")
                    return False, error
            else:
                logger.warning(f"❌ خطای HTTP: {r.status_code}")
                return False, f"HTTP {r.status_code}"

        except httpx.TimeoutException:
            return False, "Timeout — اتصال به تلگرام ممکن نیست"
        except Exception as e:
            logger.exception("خطا در تست تلگرام")
            return False, str(e)