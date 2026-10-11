#!/usr/bin/env python
"""اجرای Telegram Bot از ریشه‌ی پروژه."""

import asyncio
import sys
from pathlib import Path

# ۱. اضافه کردن root به sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ۲. لود .env (قبل از import main)
from dotenv import load_dotenv
load_dotenv()

# ۳. حالا import کن
from scripts.bot.main import main


if __name__ == "__main__":
    asyncio.run(main())