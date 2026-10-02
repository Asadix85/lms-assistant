"""Notifier برای اعلان ویندوز."""

import sys

from loguru import logger

from src.services.sync_result import SyncResult


class Notifier:
    """ارسال اعلان ویندوز."""

    def __init__(self, app_id: str = "LMS Assistant") -> None:
        self.app_id = app_id
        self._enabled = sys.platform == "win32"

        if not self._enabled:
            logger.info("Notifier فقط روی ویندوز کار می‌کند")

    def notify_sync_result(self, result: SyncResult) -> bool:
        """اعلان نتیجه Sync."""
        if not self._enabled:
            return False

        if result.has_error:
            return self._notify(
                title="❌ خطا در Sync",
                message=result.error or "خطای ناشناخته",
            )

        if result.is_first_sync:
            return self._notify(
                title="🎉 اولین Sync موفق!",
                message=(
                    f"{result.courses_new} درس، "
                    f"{result.contents_new} فایل، "
                    f"{result.events_new} رویداد"
                ),
            )

        if result.total_new == 0:
            return self._notify(
                title="✨ بدون تغییر",
                message="هیچ چیز جدیدی در LMS نیست",
            )

        # موارد جدید
        parts = []
        if result.courses_new:
            parts.append(f"{result.courses_new} درس")
        if result.contents_new:
            parts.append(f"{result.contents_new} فایل")
        if result.events_new:
            parts.append(f"{result.events_new} رویداد")

        message = "📢 " + "، ".join(parts) + " جدید"

        return self._notify(
            title="📢 تغییرات جدید در LMS",
            message=message,
        )

    def _notify(self, title: str, message: str) -> bool:
        """ارسال اعلان."""
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id=self.app_id,
                title=title,
                msg=message,
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()

            logger.debug(f"اعلان: {title} - {message}")
            return True

        except Exception as e:
            logger.warning(f"خطا در اعلان: {e}")
            return False

    def notify_simple(self, title: str, message: str) -> bool:
        """اعلان ساده."""
        return self._notify(title, message)