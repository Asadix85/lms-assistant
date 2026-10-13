"""خلاصه‌ی روزانه — امروز + فردا."""

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


def fmt_time(dt_str: str) -> str:
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
        return

    if not DB_FILE.exists():
        return

    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    # === تکالیف امروز ===
    today_assignments = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline < ? "
        "ORDER BY deadline",
        (today_start.isoformat(), tomorrow_start.isoformat()),
    ).fetchall()

    # === تکالیف فردا ===
    tomorrow_assignments = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline < ? "
        "ORDER BY deadline",
        (tomorrow_start.isoformat(), tomorrow_end.isoformat()),
    ).fetchall()

    # === رویدادهای امروز ===
    today_events = conn.execute(
        "SELECT title, start_at FROM events "
        "WHERE start_at >= ? AND start_at < ? "
        "ORDER BY start_at",
        (today_start.isoformat(), tomorrow_start.isoformat()),
    ).fetchall()

    conn.close()

    # === تاریخ شمسی ===
    jd_now = jdatetime.datetime.fromgregorian(datetime=now)
    jd_tomorrow = jdatetime.datetime.fromgregorian(datetime=now + timedelta(days=1))

    lines = [
        "☀️ <b>صبح بخیر!</b>",
        f"📅 {jd_now.strftime('%A، %d %B %Y')}",
        "",
    ]

    # === امروز ===
    if today_assignments or today_events:
        lines.append(f"📌 <b>برنامه‌ی امروز:</b>")

        if today_assignments:
            lines.append(f"📋 <b>{len(today_assignments)} تکلیف:</b>")
            for a in today_assignments:
                lines.append(f"  • {a['title'][:50]}")
                if a["deadline"]:
                    lines.append(f"    ⏰ {fmt_time(a['deadline'])}")
            lines.append("")

        if today_events:
            lines.append(f"📅 <b>{len(today_events)} رویداد:</b>")
            for e in today_events:
                lines.append(f"  • {e['title'][:50]}")
                if e["start_at"]:
                    lines.append(f"    ⏰ {fmt_time(e['start_at'])}")
            lines.append("")
    else:
        lines.append("✨ امروز هیچ برنامه‌ای نداری!")
        lines.append("")

    # === فردا ===
    if tomorrow_assignments:
        lines.append(f"📅 <b>فردا ({jd_tomorrow.strftime('%A، %d %B')}):</b>")
        lines.append(f"📋 <b>{len(tomorrow_assignments)} تکلیف:</b>")
        for a in tomorrow_assignments:
            lines.append(f"  • {a['title'][:50]}")
            if a["deadline"]:
                lines.append(f"    ⏰ {fmt_time(a['deadline'])}")
        lines.append("")

    if send_telegram(token, chat_id, "\n".join(lines)):
        print("✅ خلاصه ارسال شد")


if __name__ == "__main__":
    main()