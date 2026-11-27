"""یادآوری ددلاین‌های نزدیک (۳ روز مانده) — برای همهٔ کاربران."""
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


def to_jalali(dt_str: str | None) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        return jd.strftime("%d %B — %H:%M")
    except (ValueError, TypeError):
        return dt_str[:16]


def _urgency(hours_left: float) -> str:
    if hours_left < 6:
        return "🔴"
    if hours_left < 24:
        return "🟠"
    if hours_left < 48:
        return "🟡"
    return "🟢"


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
    users = conn.execute(
        "SELECT id, full_name, lms_username FROM users WHERE is_active = 1"
    ).fetchall()

    any_sent = False
    for user in users:
        uid = user["id"]
        name = (user["full_name"] or user["lms_username"] or "کاربر").split()[0]

        urgent_asg = conn.execute(
            "SELECT title, deadline FROM assignments "
            "WHERE user_id = ? AND is_done = 0 AND deadline IS NOT NULL "
            "  AND deadline >= ? AND deadline <= ? ORDER BY deadline",
            (uid, now.isoformat(), three_days_later.isoformat()),
        ).fetchall()

        urgent_quera = []
        try:
            urgent_quera = conn.execute(
                "SELECT name, finish_time FROM quera_assignments "
                "WHERE user_id = ? AND finish_time IS NOT NULL "
                "  AND finish_time >= ? AND finish_time <= ? ORDER BY finish_time",
                (uid, now.isoformat(), three_days_later.isoformat()),
            ).fetchall()
        except sqlite3.OperationalError:
            pass

        if not urgent_asg and not urgent_quera:
            continue

        lines = [
            f"⚠️ <b>یادآوری ددلاین‌ها — {name}</b>",
            "",
        ]

        if urgent_asg:
            lines.append(f"📋 <b>{len(urgent_asg)} تکلیف LMS:</b>")
            for a in urgent_asg:
                try:
                    dt = datetime.fromisoformat(a["deadline"])
                    hours_left = (dt - now).total_seconds() / 3600
                    icon = _urgency(hours_left)
                    days = max(0, int(hours_left // 24))
                    lines.append(f"  {icon} {a['title'][:50]}")
                    lines.append(f"    ⏰ {to_jalali(a['deadline'])} ({days} روز)")
                except (ValueError, TypeError):
                    lines.append(f"  ⚪ {a['title'][:50]}")
            lines.append("")

        if urgent_quera:
            lines.append(f"🎯 <b>{len(urgent_quera)} تمرین Quera:</b>")
            for q in urgent_quera:
                try:
                    dt = datetime.fromisoformat(q["finish_time"])
                    hours_left = (dt - now).total_seconds() / 3600
                    icon = _urgency(hours_left)
                    days = max(0, int(hours_left // 24))
                    lines.append(f"  {icon} {q['name'][:50]}")
                    lines.append(f"    ⏰ {to_jalali(q['finish_time'])} ({days} روز)")
                except (ValueError, TypeError):
                    lines.append(f"  ⚪ {q['name'][:50]}")
            lines.append("")

        if send_telegram(token, chat_id, "\n".join(lines)):
            any_sent = True

    conn.close()
    print("✅ یادآوری ارسال شد" if any_sent else "✨ هیچ ددلاین نزدیکی نیست")


if __name__ == "__main__":
    main()