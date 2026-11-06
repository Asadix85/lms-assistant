"""Path helpers برای اجرا از EXE یا Python."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def is_frozen() -> bool:
    """آیا در EXE اجرا می‌شه؟"""
    return getattr(sys, "frozen", False)


def get_base_dir() -> Path:
    """پوشه‌ی ریشه برنامه (کنار EXE یا ریشه‌ی پروژه)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def get_bundle_dir() -> Path:
    """مسیر منابع بسته‌بندی‌شده (assets, schema, ...).

    - حالت توسعه: ریشه‌ی پروژه
    - onefile: sys._MEIPASS
    - onedir (PyInstaller 6+): معمولاً _internal کنار exe
    """
    if not is_frozen():
        return get_base_dir()

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)

    base = get_base_dir()
    internal = base / "_internal"
    if internal.is_dir():
        return internal
    return base


def get_asset_path(relative: str) -> Path:
    """مسیر یه asset (font, icon, ...)."""
    return get_bundle_dir() / "assets" / relative


def _try_mkdir(path: Path) -> bool:
    """سعی در ساخت پوشه؛ در صورت موفقیت True."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        # تست نوشتن واقعی
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def get_data_dir() -> Path:
    """پوشه‌ی داده‌ی قابل‌نوشتن کاربر (دیتابیس، کش، ...).

    ترتیب تلاش در حالت EXE:
      1) %LOCALAPPDATA%\\LMSAssistant\\data
      2) %USERPROFILE%\\LMSAssistant\\data
      3) کنار EXE → data\\
      4) %TEMP%\\LMSAssistant\\data
    """
    if not is_frozen():
        path = get_base_dir() / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    candidates: list[Path] = []

    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(Path(local) / "LMSAssistant" / "data")

    home = Path.home()
    candidates.append(home / "LMSAssistant" / "data")
    candidates.append(get_base_dir() / "data")

    tmp = os.environ.get("TEMP") or tempfile.gettempdir()
    candidates.append(Path(tmp) / "LMSAssistant" / "data")

    for path in candidates:
        if _try_mkdir(path):
            return path

    # آخرین تلاش: tempfile مخصوص این session
    fallback = Path(tempfile.mkdtemp(prefix="lms_assistant_"))
    return fallback


def get_data_path(relative: str = "") -> Path:
    """مسیر یه فایل توی پوشه‌ی data."""
    if not relative:
        return get_data_dir()
    return get_data_dir() / relative


def get_env_path() -> Path:
    """مسیر `.env` — در EXE کنار داده‌ی کاربر (بدون اجبار mkdir اضافی)."""
    if is_frozen():
        # فقط parent را می‌خواهیم؛ get_data_dir خودش mkdir امن دارد
        return get_data_dir().parent / ".env"
    return get_base_dir() / ".env"
