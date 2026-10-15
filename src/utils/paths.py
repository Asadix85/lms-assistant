"""Path helpers برای اجرا از EXE یا Python."""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """آیا در EXE اجرا می‌شه؟"""
    return getattr(sys, "frozen", False)


def get_base_dir() -> Path:
    """پوشه‌ی ریشه (کنار EXE یا ریشه‌ی پروژه)."""
    if is_frozen():
        # EXE → پوشه‌ی EXE
        base = Path(sys.executable).parent
        print(f"🔍 [FROZEN] sys.executable: {sys.executable}")
        print(f"🔍 [FROZEN] base_dir: {base}")
        print(f"🔍 [FROZEN] assets: {base / 'assets'}")
        print(f"🔍 [FROZEN] assets exists: {(base / 'assets').exists()}")
        return base
    else:
        # Python → ریشه‌ی پروژه
        base = Path(__file__).parent.parent.parent
        return base


def get_asset_path(relative: str) -> Path:
    """مسیر یه asset (font, icon, ...).

    Args:
        relative: مسیر نسبی به `assets/` (مثل "icons/app.png")

    Returns:
        مسیر کامل
    """
    return get_base_dir() / "assets" / relative


def get_data_path(relative: str = "") -> Path:
    """مسیر یه فایل توی `data/`.

    Args:
        relative: مسیر نسبی به `data/` (مثل "lms.db")

    Returns:
        مسیر کامل
    """
    return get_base_dir() / "data" / relative


def get_env_path() -> Path:
    """مسیر `.env`."""
    return get_base_dir() / ".env"