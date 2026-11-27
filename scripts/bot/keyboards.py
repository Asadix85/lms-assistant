"""دکمه‌های inline بات — چیدمان بهینه برای موبایل."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_dashboard() -> InlineKeyboardMarkup:
    """داشبورد اصلی — ۲ ستون × ۳ ردیف."""
    keyboard = [
        [
            InlineKeyboardButton(text="📋 تکالیف امروز", callback_data="today"),
            InlineKeyboardButton(text="📅 ددلاین‌های هفته", callback_data="week"),
        ],
        [
            InlineKeyboardButton(text="🎯 کوئرا", callback_data="quera"),
            InlineKeyboardButton(text="📢 پست‌ها", callback_data="posts"),
        ],
        [
            InlineKeyboardButton(text="📊 آمار", callback_data="stats"),
            InlineKeyboardButton(text="🔄 به‌روزرسانی", callback_data="refresh"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_button() -> InlineKeyboardMarkup:
    """دکمه بازگشت + refresh در کنار."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="back"),
            InlineKeyboardButton(text="🔄 تازه‌سازی", callback_data="refresh"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)