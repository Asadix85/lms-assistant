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

        # ⚠️ خطا
        if result.has_error:
            return self._notify(
                title="❌ خطا در Sync",
                message=result.error or "خطای ناشناخته",
                icon="error",
            )

        # ⚠️ اولین Sync
        if result.is_first_sync:
            return self._notify(
                title="🎉 اولین Sync موفق!",
                message=(
                    f"{result.courses_new} درس، "
                    f"{result.contents_new} فایل، "
                    f"{result.events_new} رویداد"
                ),
                icon="success",
            )

        # ⚠️ بدون تغییر
        if result.total_new == 0:
            return self._notify(
                title="✨ بدون تغییر",
                message="هیچ چیز جدیدی در LMS نیست",
                icon="info",
            )

        # ⚠️ موارد جدید (با رنگ موفق)
        parts = []
        if result.courses_new:
            parts.append(f"{result.courses_new} درس")
        if result.contents_new:
            parts.append(f"{result.contents_new} فایل")
        if result.events_new:
            parts.append(f"{result.events_new} رویداد")
        if result.assignments_new:
            parts.append(f"{result.assignments_new} تکلیف")

        message = "📢 " + "، ".join(parts) + " جدید"

        return self._notify(
            title="📢 تغییرات جدید در LMS",
            message=message,
            icon="info",
        )

    def _notify(self, title: str, message: str, icon: str = "info") -> bool:
        """ارسال اعلان."""
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id=self.app_id,
                title=title,
                msg=message,
                duration="short",
                icon=self._get_icon_path(icon),
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()

            logger.debug(f"اعلان: {title} - {message}")
            return True

        except Exception as e:
            logger.warning(f"خطا در اعلان: {e}")
            return False

    def _get_icon_path(self, icon_type: str) -> str:
        """مسیر آیکون برای اعلان."""
        from pathlib import Path

        icon_map = {
            "success": "circle-check.svg",
            "error": "circle-xmark.svg",
            "warning": "triangle-exclamation.svg",
            "info": "circle-info.svg",
        }

        icon_name = icon_map.get(icon_type, "circle-info.svg")
        icon_path = Path("assets/icons") / icon_name

        # winotify فقط PNG و ICO می‌خواد (SVG پشتیبانی نمی‌شه)
        # برای سادگی، از PNG استفاده می‌کنیم
        png_name = icon_name.replace(".svg", ".png")
        png_path = Path("assets/icons") / png_name

        if png_path.exists():
            return str(png_path.absolute())

        return ""

    def notify_simple(self, title: str, message: str) -> bool:
        """اعلان ساده."""
        return self._notify(title, message, icon="info")