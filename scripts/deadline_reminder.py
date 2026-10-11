"""یادآوری ددلاین‌های نزدیک (۳ روز مانده)."""

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


def to_jalali(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        return jd.strftime("%d %B — %H:%M")
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
    three_days_later = now + timedelta(days=3)

    # === تکالیفی که ۳ روز آینده ددلاین دارن ===
    urgent_assignments = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline <= ? "
        "ORDER BY deadline",
        (now.isoformat(), three_days_later.isoformat()),
    ).fetchall()

    # === تمرین‌های Quera ===
    urgent_quera = conn.execute(
        "SELECT name, finish_time FROM quera_assignments "
        "WHERE finish_time >= ? AND finish_time <= ? "
        "ORDER BY finish_time",
        (now.isoformat(), three_days_later.isoformat()),
    ).fetchall()

    conn.close()

    total = len(urgent_assignments) + len(urgent_quera)
    if total == 0:
        print("✨ هیچ ددلاین نزدیکی نیست")
        return

    lines = ["⚠️ <b>یادآوری: ددلاین‌های نزدیک!</b>", ""]

    if urgent_assignments:
        lines.append(f"📋 <b>{len(urgent_assignments)} تکلیف LMS:</b>")
        for a in urgent_assignments:
            days_left = (datetime.fromisoformat(a["deadline"]) - now).days
            lines.append(f"  • {a['title'][:50]}")
            lines.append(f"    ⏰ {to_jalali(a['deadline'])} ({days_left} روز)")
        lines.append("")

    if urgent_quera:
        lines.append(f"🎯 <b>{len(urgent_quera)} تمرین Quera:</b>")
        for q in urgent_quera:
            days_left = (datetime.fromisoformat(q["finish_time"]) - now).days
            lines.append(f"  • {q['name'][:50]}")
            lines.append(f"    ⏰ {to_jalali(q['finish_time'])} ({days_left} روز)")
        lines.append("")

    message = "\n".join(lines)

    if send_telegram(token, chat_id, message):
        print(f"✅ {total} یادآوری ارسال شد")


if __name__ == "__main__":
    main()