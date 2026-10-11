"""هندلرهای ربات."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from scripts.bot import queries
from scripts.bot.keyboards import back_button, main_dashboard


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """دستور /start."""
    text = (
        "🎓 <b>LMS Assistant</b>\n\n"
        "سلام! 👋\n"
        "چه کاری برات انجام بدم؟"
    )
    await message.answer(text, reply_markup=main_dashboard())


@router.callback_query(F.data == "back")
async def cb_back(callback: CallbackQuery) -> None:
    """بازگشت به داشبورد."""
    await callback.message.edit_text(
        "🎓 <b>LMS Assistant</b>\n\nچه کاری برات انجام بدم؟",
        reply_markup=main_dashboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "today")
async def cb_today(callback: CallbackQuery) -> None:
    """تکالیف امروز."""
    text = queries.get_today_assignments()
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "week")
async def cb_week(callback: CallbackQuery) -> None:
    """ددلاین‌های هفته."""
    text = queries.get_week_deadlines()
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "quera")
async def cb_quera(callback: CallbackQuery) -> None:
    """تمرین‌های Quera."""
    text = queries.get_quera_assignments()
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "posts")
async def cb_posts(callback: CallbackQuery) -> None:
    """پست‌های اخیر."""
    text = queries.get_recent_posts()
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery) -> None:
    """آمار کلی."""
    text = queries.get_stats()
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "refresh")
async def cb_refresh(callback: CallbackQuery) -> None:
    """بروزرسانی."""
    # ⚠️ اینجا می‌تونه sync رو trigger کنه (اختیاری)
    text = "🔄 <b>بروزرسانی</b>\n\nآخرین Sync: ...\n\nداده‌های جدید آماده‌ست."
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer("✅ بروزرسانی شد")