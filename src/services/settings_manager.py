"""Settings Manager: ذخیره و بازیابی تنظیمات."""

from pathlib import Path

from loguru import logger

from src.storage.database import Database
from src.storage.repositories import SettingRepository


class SettingsManager:
    """مدیریت تنظیمات ذخیره‌شده."""

    DB_PATH = "data/lms.db"

    # کلیدهای تنظیمات
    KEY_THEME = "app_theme"
    KEY_WINDOW_GEOMETRY = "window_geometry"
    KEY_WINDOW_STATE = "window_state"
    KEY_LAST_PAGE = "last_page"
    KEY_SYNC_COURSES = "sync_courses"
    KEY_SYNC_CONTENTS = "sync_contents"
    KEY_SYNC_EVENTS = "sync_events"
    KEY_SYNC_POSTS = "sync_posts"
    KEY_SYNC_ASSIGNMENTS = "sync_assignments"
    KEY_SYNC_MEMBERS = "sync_members"

    @classmethod
    def get_sync_settings(cls) -> dict:
        """خواندن همه‌ی تنظیمات Sync."""
        return {
            "courses": cls.load(cls.KEY_SYNC_COURSES, "true") == "true",
            "contents": cls.load(cls.KEY_SYNC_CONTENTS, "true") == "true",
            "events": cls.load(cls.KEY_SYNC_EVENTS, "true") == "true",
            "posts": cls.load(cls.KEY_SYNC_POSTS, "true") == "true",
            "assignments": cls.load(cls.KEY_SYNC_ASSIGNMENTS, "true") == "true",
            "members": cls.load(cls.KEY_SYNC_MEMBERS, "false") == "false",  # پیش‌فرض: خاموش
        }

    @classmethod
    def save_sync_settings(cls, settings: dict) -> None:
        """ذخیره‌ی تنظیمات Sync."""
        for key, value in settings.items():
            cls.save(f"sync_{key}", "true" if value else "false")

    @classmethod
    def save(cls, key: str, value: str) -> None:
        """ذخیره‌ی یک تنظیم."""
        try:
            with Database(cls.DB_PATH) as db:
                db.init_schema()
                SettingRepository(db).set(key, value)
                logger.debug(f"ذخیره: {key} = {value[:50]}")
        except Exception as e:
            logger.warning(f"خطا در ذخیره {key}: {e}")

    @classmethod
    def load(cls, key: str, default: str | None = None) -> str | None:
        """خواندن یک تنظیم."""
        try:
            with Database(cls.DB_PATH) as db:
                db.init_schema()
                value = SettingRepository(db).get(key, default)
                logger.debug(f"بازیابی: {key} = {value[:50] if value else None}")
                return value
        except Exception as e:
            logger.warning(f"خطا در بازیابی {key}: {e}")
            return default

    # === Shortcuts ===

    @classmethod
    def save_theme(cls, mode: str) -> None:
        cls.save(cls.KEY_THEME, mode)

    @classmethod
    def load_theme(cls, default: str = "light") -> str:
        return cls.load(cls.KEY_THEME, default) or default

    @classmethod
    def save_geometry(cls, geometry_bytes: bytes) -> None:
        """ذخیره‌ی geometry پنجره."""
        import base64
        encoded = base64.b64encode(geometry_bytes).decode("utf-8")
        cls.save(cls.KEY_WINDOW_GEOMETRY, encoded)

    @classmethod
    def load_geometry(cls) -> bytes | None:
        """بازیابی geometry پنجره."""
        encoded = cls.load(cls.KEY_WINDOW_GEOMETRY)
        if not encoded:
            return None
        import base64
        try:
            return base64.b64decode(encoded.encode("utf-8"))
        except Exception:
            return None

    @classmethod
    def save_last_page(cls, page_key: str) -> None:
        cls.save(cls.KEY_LAST_PAGE, page_key)

    @classmethod
    def load_last_page(cls, default: str = "dashboard") -> str:
        return cls.load(cls.KEY_LAST_PAGE, default) or default