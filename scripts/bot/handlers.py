"""هندلرهای بات — پیام‌های کاربرپسند و هندل خطای یکپارچه."""
from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from scripts.bot import queries
from scripts.bot.keyboards import back_button, main_dashboard


router = Router()


def _greet() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "☀️ صبح بخیر!"
    if 12 <= h < 17:
        return "🌤 ظهر بخیر!"
    if 17 <= h < 21:
        return "🌇 عصر بخیر!"
    return "🌙 شب بخیر!"


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    greet = _greet()
    text = (
        f"{greet}\n\n"
        "🎓 <b>LMS Assistant</b>\n\n"
        "دستیار شخصی سامانهٔ آموزشی دانشگاه اصفهان.\n"
        "چه کاری برات انجام بدم؟"
    )
    await message.answer(text, reply_markup=main_dashboard(), disable_web_page_preview=True)


async def _safe_answer(cb: CallbackQuery, fetcher, title: str) -> None:
    """فراخوانی امن fetcher و edit پیام. خطا را به کاربر نشان می‌دهد نه crash."""
    try:
        text = fetcher()
        body = f"<b>{title}</b>\n\n{text}" if not text.startswith("<b>") else text
    except FileNotFoundError as e:
        body = f"❌ {e}\n\nابتدا یک sync از داشبورد وب بزن."
    except Exception as e:
        body = f"❌ خطا: <code>{type(e).__name__}: {str(e)[:120]}</code>"

    try:
        await cb.message.edit_text(
            body,
            reply_markup=back_button(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception as e:
        # اگر edit نشد (مثلاً متن یکسان بود)، یک پیام جدید بفرست
        await cb.message.answer(body, reply_markup=back_button(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "back")
async def cb_back(callback: CallbackQuery) -> None:
    greet = _greet()
    await callback.message.edit_text(
        f"{greet}\n\n🎓 <b>LMS Assistant</b>\n\nچه کاری برات انجام بدم؟",
        reply_markup=main_dashboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "today")
async def cb_today(callback: CallbackQuery) -> None:
    await _safe_answer(callback, queries.get_today_assignments, "📋 تکالیف امروز")


@router.callback_query(F.data == "week")
async def cb_week(callback: CallbackQuery) -> None:
    await _safe_answer(callback, queries.get_week_deadlines, "📅 ددلاین‌های هفته")


@router.callback_query(F.data == "quera")
async def cb_quera(callback: CallbackQuery) -> None:
    await _safe_answer(callback, queries.get_quera_assignments, "🎯 کوئرا")


@router.callback_query(F.data == "posts")
async def cb_posts(callback: CallbackQuery) -> None:
    await _safe_answer(callback, queries.get_recent_posts, "📢 پست‌های اخیر")


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery) -> None:
    await _safe_answer(callback, queries.get_stats, "📊 آمار")


@router.callback_query(F.data == "refresh")
async def cb_refresh(callback: CallbackQuery) -> None:
    """نمایش آخرین زمان sync از جدول settings."""
    import sqlite3
    from pathlib import Path

    last_sync = "نامشخص"
    try:
        conn = sqlite3.connect(str(Path("data/lms.db")))
        conn.row_factory = sqlite3.Row
        # آخرین sync موفق را از جدول settings هر کاربر پیدا کن
        row = conn.execute(
            "SELECT value, user_id FROM settings WHERE key = 'last_sync_at' "
            "ORDER BY value DESC LIMIT 1"
        ).fetchone()
        if row and row["value"]:
            last_sync = row["value"][:16].replace("T", " ")
        conn.close()
    except Exception:
        pass

    text = (
        "🔄 <b>به‌روزرسانی</b>\n\n"
        f"🕒 آخرین sync: <code>{last_sync}</code>\n\n"
        "برای اجرای sync کامل، از دکمهٔ «همگام‌سازی» در داشبورد وب استفاده کن. "
        "این دکمه فقط زمان آخرین sync را نشان می‌دهد."
    )
    try:
        await callback.message.edit_text(
            text, reply_markup=back_button(), parse_mode="HTML", disable_web_page_preview=True
        )
    except Exception:
        await callback.message.answer(text, reply_markup=back_button(), parse_mode="HTML")
    await callback.answer("ℹ️ وضعیت بارگذاری شد")