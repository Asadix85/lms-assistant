"""پیکربندی مشترک تست‌ها.

تست‌های integration که به اعتبارنامه‌ی واقعی LMS نیاز دارند،
در صورت نبود LMS_USERNAME/LMS_PASSWORD خودکار skip می‌شوند
(مثلاً در CI یا روی سیستم تازه).
"""

import os

import pytest


def pytest_runtest_setup(item: pytest.Item) -> None:
    """اگر تست به environ واقعی LMS نیاز داشت و نبود، skip کن."""
    if not (os.environ.get("LMS_USERNAME") and os.environ.get("LMS_PASSWORD")):
        # فقط تست‌هایی که واقعاً از environ استفاده می‌کنند skip شوند؛
        # ساده‌ترین راه: بررسی source فایل تست
        src = ""
        try:
            src = item.path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
        if "LMS_USERNAME" in src:
            pytest.skip("اعتبارنامه‌ی LMS (LMS_USERNAME/LMS_PASSWORD) تنظیم نشده — تست integration رد شد")
