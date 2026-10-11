"""Telegram Bot برای LMS Assistant (با Cloudflare Proxy)."""

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from scripts.bot.handlers import router


# ⚠️ آدرس Worker
PROXY_URL = os.environ.get(
    "TELEGRAM_PROXY_URL",
    "https://lms-proxy.mohammad8asadi5.workers.dev",
)


async def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN تنظیم نشده")
        return

    # === استفاده از Cloudflare Worker ===
    api_server = TelegramAPIServer.from_base(PROXY_URL)

    # === Session با Worker ===
    session = AiohttpSession(api=api_server)

    bot = Bot(
        token=token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    print(f"🤖 Bot started via {PROXY_URL}...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())