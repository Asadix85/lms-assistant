"""بررسی تغییرات LMS + Quera و ارسال نوتیفیکیشن به تلگرام.

این اسکریپت توی GitHub Actions اجرا می‌شه (هر ۲ ساعت).
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

import jdatetime
import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
DB_FILE = Path("data/lms.db")


def to_jalali(dt_str: str) -> str:
    """تبدیل ISO datetime به شمسی (رشته)."""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        return jd.strftime("%d %B %Y — %H:%M")
    except Exception:
        return dt_str[:16]


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """ارسال پیام به تلگرام."""
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
    except requests.HTTPError as e:
        print(f"❌ خطای HTTP: {e}")
        print(f"   پاسخ: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


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

    # === تکالیف جدید LMS ===
    try:
        assignments = conn.execute(
            "SELECT id, title, deadline FROM assignments "
            "WHERE is_new = 1 ORDER BY deadline LIMIT 10"
        ).fetchall()
    except sqlite3.OperationalError:
        assignments = []

    # === تمرین‌های جدید Quera ===
    try:
        quera = conn.execute(
            "SELECT id, name, finish_time FROM quera_assignments "
            "WHERE is_new = 1 ORDER BY finish_time LIMIT 10"
        ).fetchall()
    except sqlite3.OperationalError:
        quera = []

    # === پست‌های جدید ===
    try:
        posts = conn.execute(
            "SELECT id, author, text FROM posts "
            "WHERE is_new = 1 ORDER BY posted_at DESC LIMIT 5"
        ).fetchall()
    except sqlite3.OperationalError:
        posts = []

    # === رویدادهای جدید ===
    try:
        events = conn.execute(
            "SELECT id, title, start_at FROM events "
            "WHERE is_new = 1 ORDER BY start_at LIMIT 5"
        ).fetchall()
    except sqlite3.OperationalError:
        events = []

    total = len(assignments) + len(quera) + len(posts) + len(events)
    if total == 0:
        print("✨ هیچ تغییر جدیدی نیست")
        conn.close()
        return

    print(f"🔔 {total} تغییر جدید پیدا شد")

    # === ساخت پیام ===
    lines = ["🔔 <b>تغییرات جدید در LMS Assistant</b>", ""]

    # === تکالیف LMS ===
    if assignments:
        lines.append(f"📋 <b>{len(assignments)} تکلیف جدید LMS:</b>")
        for a in assignments[:5]:
            lines.append(f"  • {a['title'][:60]}")
            if a["deadline"]:
                lines.append(f"    ⏰ {to_jalali(a['deadline'])}")
        lines.append("")

    # === تمرین‌های Quera ===
    if quera:
        lines.append(f"🎯 <b>{len(quera)} تمرین جدید Quera:</b>")
        for q in quera[:5]:
            lines.append(f"  • {q['name'][:60]}")
            if q["finish_time"]:
                lines.append(f"    ⏰ {to_jalali(q['finish_time'])}")
        lines.append("")

    # === پست‌های جدید ===
    if posts:
        lines.append(f"📢 <b>{len(posts)} پیام جدید:</b>")
        for p in posts[:3]:
            text = p["text"][:80].replace("\n", " ")
            lines.append(f"  • <b>{p['author']}</b>: {text}...")
        lines.append("")

    # === رویدادهای جدید ===
    if events:
        lines.append(f"📅 <b>{len(events)} رویداد جدید:</b>")
        for e in events[:3]:
            lines.append(f"  • {e['title'][:60]}")
            if e["start_at"]:
                lines.append(f"    ⏰ {to_jalali(e['start_at'])}")
        lines.append("")

    # === Footer ===
    now = datetime.now()
    jd = jdatetime.datetime.fromgregorian(datetime=now)
    lines.append(f"⏱️ {jd.strftime('%Y/%m/%d — %H:%M')}")

    message = "\n".join(lines)

    # === ارسال ===
    if send_telegram(token, chat_id, message):
        print("✅ نوتیفیکیشن ارسال شد")
        # ⚠️ is_new رو صفر نمی‌کنیم چون دیتابیس لوکال دست‌نخورده می‌مونه
    else:
        print("❌ خطا در ارسال")

    conn.close()


if __name__ == "__main__":
    main()