"""خلاصه‌ی روزانه — هر روز صبح ساعت ۸."""

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
        print(f"✅ پیام ارسال شد ({len(text)} کاراکتر)")
        return True
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False


def to_jalali(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        return jd.strftime("%H:%M")
    except Exception:
        return dt_str[:16]


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Token یا Chat ID نیست")
        return

    if not DB_FILE.exists():
        print(f"❌ دیتابیس پیدا نشد: {DB_FILE}")
        return

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    week_later = now + timedelta(days=7)

    # === تکالیف امروز ===
    today_assignments = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline < ? "
        "ORDER BY deadline",
        (today_start.isoformat(), today_end.isoformat()),
    ).fetchall()

    # === رویدادهای امروز ===
    today_events = conn.execute(
        "SELECT title, start_at FROM events "
        "WHERE start_at >= ? AND start_at < ? "
        "ORDER BY start_at",
        (today_start.isoformat(), today_end.isoformat()),
    ).fetchall()

    # === ددلاین‌های هفته ===
    week_count = conn.execute(
        "SELECT COUNT(*) as n FROM assignments "
        "WHERE deadline >= ? AND deadline <= ?",
        (now.isoformat(), week_later.isoformat()),
    ).fetchone()["n"]

    # === تمرین‌های Quera ===
    quera_count = conn.execute(
        "SELECT COUNT(*) as n FROM quera_assignments"
    ).fetchone()["n"]

    conn.close()

    # === تاریخ شمسی ===
    jd = jdatetime.datetime.fromgregorian(datetime=now)

    lines = [
        "☀️ <b>صبح بخیر!</b>",
        f"📅 {jd.strftime('%A، %d %B %Y')}",
        "",
    ]

    # === تکالیف امروز ===
    if today_assignments:
        lines.append(f"📋 <b>{len(today_assignments)} تکلیف امروز:</b>")
        for a in today_assignments:
            lines.append(f"  • {a['title'][:50]}")
            if a["deadline"]:
                lines.append(f"    ⏰ {to_jalali(a['deadline'])}")
        lines.append("")
    else:
        lines.append("✨ تکلیفی برای امروز نداری!")
        lines.append("")

    # === رویدادهای امروز ===
    if today_events:
        lines.append(f"📅 <b>{len(today_events)} رویداد امروز:</b>")
        for e in today_events:
            lines.append(f"  • {e['title'][:50]}")
            if e["start_at"]:
                lines.append(f"    ⏰ {to_jalali(e['start_at'])}")
        lines.append("")

    # === خلاصه ===
    lines.append("📊 <b>خلاصه:</b>")
    lines.append(f"  • {week_count} ددلاین در هفته")
    lines.append(f"  • {quera_count} تمرین Quera")

    message = "\n".join(lines)

    if send_telegram(token, chat_id, message):
        print("✅ خلاصه ارسال شد")


if __name__ == "__main__":
    main()