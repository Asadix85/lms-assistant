#!/usr/bin/env python
"""اجرای Telegram Bot از ریشهٔ پروژه با بارگذاری صحیح env."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# ۱) اضافه کردن root به sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ۲) لود .env پیش از import main
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from scripts.bot.main import main  # noqa: E402


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 بات با درخواست کاربر متوقف شد")