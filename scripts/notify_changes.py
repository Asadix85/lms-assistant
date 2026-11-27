"""اعلان تغییرات جدید به همهٔ کاربران فعال با state جدا برای جلوگیری از تکرار."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

import jdatetime
import requests

from state_manager import filter_new, load_state, mark_notified, save_state


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
DB_FILE = Path("data/lms.db")


def to_jalali(dt_str: str | None) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        jd = jdatetime.datetime.fromgregorian(datetime=dt)
        return jd.strftime("%d %B %Y — %H:%M")
    except (ValueError, TypeError):
        return str(dt_str)[:16]


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
    except requests.HTTPError as e:
        print(f"❌ خطای HTTP: {e}")
        try:
            print(f"   پاسخ: {r.text[:200]}")
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False


def _fetch_safe(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده")
        return
    if not DB_FILE.exists():
        print(f"❌ دیتابیس پیدا نشد: {DB_FILE}")
        return

    state = load_state()
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    users = conn.execute(
        "SELECT id, full_name, lms_username FROM users WHERE is_active = 1"
    ).fetchall()
    if not users:
        conn.close()
        return

    any_sent = False
    for user in users:
        uid = user["id"]
        name = (user["full_name"] or user["lms_username"] or "کاربر").split()[0]

        asg = _fetch_safe(
            conn,
            "SELECT id, title, deadline FROM assignments "
            "WHERE user_id = ? AND is_new = 1 ORDER BY deadline LIMIT 20",
            (uid,),
        )
        quera = _fetch_safe(
            conn,
            "SELECT id, name, finish_time FROM quera_assignments "
            "WHERE user_id = ? AND is_new = 1 ORDER BY finish_time LIMIT 20",
            (uid,),
        )
        posts = _fetch_safe(
            conn,
            "SELECT id, author, text FROM posts "
            "WHERE user_id = ? AND is_new = 1 ORDER BY posted_at DESC LIMIT 10",
            (uid,),
        )
        events = _fetch_safe(
            conn,
            "SELECT id, title, start_at FROM events "
            "WHERE user_id = ? AND is_new = 1 ORDER BY start_at LIMIT 10",
            (uid,),
        )

        asg = filter_new(asg, f"u{uid}:asg", state)
        quera = filter_new(quera, f"u{uid}:quera", state)
        posts = filter_new(posts, f"u{uid}:posts", state)
        events = filter_new(events, f"u{uid}:ev", state)

        total = len(asg) + len(quera) + len(posts) + len(events)
        if total == 0:
            continue

        print(f"🔔 {total} تغییر جدید برای {name}")

        lines = [f"🔔 <b>تغییرات جدید — {name}</b>", ""]

        if asg:
            lines.append(f"📋 <b>{len(asg)} تکلیف LMS:</b>")
            for a in asg[:5]:
                lines.append(f"  • {a['title'][:60]}")
                if a["deadline"]:
                    lines.append(f"    ⏰ {to_jalali(a['deadline'])}")
            lines.append("")

        if quera:
            lines.append(f"🎯 <b>{len(quera)} تمرین Quera:</b>")
            for q in quera[:5]:
                lines.append(f"  • {q['name'][:60]}")
                if q["finish_time"]:
                    lines.append(f"    ⏰ {to_jalali(q['finish_time'])}")
            lines.append("")

        if posts:
            lines.append(f"📢 <b>{len(posts)} پیام:</b>")
            for p in posts[:3]:
                text = (p["text"] or "")[:80].replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")
                lines.append(f"  • <b>{p['author'] or '—'}</b>: {text}…")
            lines.append("")

        if events:
            lines.append(f"📅 <b>{len(events)} رویداد:</b>")
            for e in events[:3]:
                lines.append(f"  • {e['title'][:60]}")
                if e["start_at"]:
                    lines.append(f"    ⏰ {to_jalali(e['start_at'])}")
            lines.append("")

        jd = jdatetime.datetime.fromgregorian(datetime=datetime.now())
        lines.append(f"⏱️ {jd.strftime('%Y/%m/%d — %H:%M')}")

        if send_telegram(token, chat_id, "\n".join(lines)):
            mark_notified(asg, f"u{uid}:asg", state)
            mark_notified(quera, f"u{uid}:quera", state)
            mark_notified(posts, f"u{uid}:posts", state)
            mark_notified(events, f"u{uid}:ev", state)
            any_sent = True

    if any_sent:
        save_state(state)
        print("✅ State آپدیت شد")

    conn.close()


if __name__ == "__main__":
    main()