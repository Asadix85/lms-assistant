"""دکمه‌های inline تلگرام."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_dashboard() -> InlineKeyboardMarkup:
    """داشبورد اصلی."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📋 تکالیف امروز",
                callback_data="today",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 ددلاین‌های هفته",
                callback_data="week",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎯 تمرین‌های Quera",
                callback_data="quera",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📢 پست‌های اخیر",
                callback_data="posts",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 آمار کلی",
                callback_data="stats",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 بروزرسانی",
                callback_data="refresh",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_button() -> InlineKeyboardMarkup:
    """دکمه بازگشت."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 بازگشت",
                callback_data="back",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)