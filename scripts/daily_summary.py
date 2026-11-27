"""خلاصهٔ روزانه — امروز + فردا، برای همهٔ کاربران فعال."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import jdatetime
import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
DB_FILE = Path("data/lms.db")


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    url = TELEGRAM_API.format(token=token)
    try:
        r = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False


def fmt_time(dt_str: str | None) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return ""


def _greet() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "☀️ صبح بخیر!"
    if 12 <= h < 17:
        return "🌤 ظهر بخیر!"
    if 17 <= h < 21:
        return "🌇 عصر بخیر!"
    return "🌙 شب بخیر!"


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده")
        return

    if not DB_FILE.exists():
        print(f"❌ دیتابیس پیدا نشد: {DB_FILE}")
        return

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # همهٔ کاربران فعال
    users = conn.execute(
        "SELECT id, full_name, lms_username FROM users WHERE is_active = 1"
    ).fetchall()
    if not users:
        conn.close()
        print("✨ هیچ کاربر فعالی نیست")
        return

    for user in users:
        uid = user["id"]
        name = user["full_name"] or user["lms_username"] or "کاربر"
        first_name = name.split()[0] if name else "کاربر"

        today_asg = conn.execute(
            "SELECT title, deadline FROM assignments "
            "WHERE user_id = ? AND is_done = 0 AND deadline IS NOT NULL "
            "  AND deadline >= ? AND deadline < ? ORDER BY deadline",
            (uid, today_start.isoformat(), tomorrow_start.isoformat()),
        ).fetchall()

        tomorrow_asg = conn.execute(
            "SELECT title, deadline FROM assignments "
            "WHERE user_id = ? AND is_done = 0 AND deadline IS NOT NULL "
            "  AND deadline >= ? AND deadline < ? ORDER BY deadline",
            (uid, tomorrow_start.isoformat(), tomorrow_end.isoformat()),
        ).fetchall()

        today_ev = conn.execute(
            "SELECT title, start_at FROM events "
            "WHERE user_id = ? AND start_at IS NOT NULL "
            "  AND start_at >= ? AND start_at < ? ORDER BY start_at",
            (uid, today_start.isoformat(), tomorrow_start.isoformat()),
        ).fetchall()

        jd_now = jdatetime.datetime.fromgregorian(datetime=now)
        jd_tomorrow = jdatetime.datetime.fromgregorian(datetime=now + timedelta(days=1))

        lines = [
            f"{_greet()} <b>{first_name}</b> 👋",
            f"📅 {jd_now.strftime('%A، %d %B %Y')}",
            "",
        ]

        if today_asg or today_ev:
            lines.append("📌 <b>برنامهٔ امروز:</b>")
            if today_asg:
                lines.append(f"📋 <b>{len(today_asg)} تکلیف:</b>")
                for a in today_asg:
                    lines.append(f"  • {a['title'][:50]}")
                    if a["deadline"]:
                        lines.append(f"    ⏰ {fmt_time(a['deadline'])}")
                lines.append("")
            if today_ev:
                lines.append(f"📅 <b>{len(today_ev)} رویداد:</b>")
                for e in today_ev:
                    lines.append(f"  • {e['title'][:50]}")
                    if e["start_at"]:
                        lines.append(f"    ⏰ {fmt_time(e['start_at'])}")
                lines.append("")
        else:
            lines.append("✨ امروز هیچ برنامه‌ای نداری!")
            lines.append("")

        if tomorrow_asg:
            lines.append(
                f"📆 <b>فردا ({jd_tomorrow.strftime('%A، %d %B')}):</b>"
            )
            lines.append(f"📋 <b>{len(tomorrow_asg)} تکلیف:</b>")
            for a in tomorrow_asg:
                lines.append(f"  • {a['title'][:50]}")
                if a["deadline"]:
                    lines.append(f"    ⏰ {fmt_time(a['deadline'])}")
            lines.append("")

        send_telegram(token, chat_id, "\n".join(lines))

    conn.close()
    print(f"✅ خلاصه برای {len(users)} کاربر ارسال شد")


if __name__ == "__main__":
    main()