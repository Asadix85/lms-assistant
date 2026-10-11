"""کوئری‌های SQLite."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path("data/lms.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_today_assignments() -> str:
    """تکالیف امروز."""
    conn = _connect()
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = today_start + timedelta(days=1)

    rows = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline < ? "
        "ORDER BY deadline",
        (today_start.isoformat(), today_end.isoformat()),
    ).fetchall()
    conn.close()

    if not rows:
        return "📋 <b>تکالیف امروز</b>\n\n✨ هیچ تکلیفی برای امروز نیست!"

    lines = ["📋 <b>تکالیف امروز</b>\n"]
    for r in rows:
        dt = datetime.fromisoformat(r["deadline"])
        lines.append(f"  • {r['title'][:60]}")
        lines.append(f"    ⏰ {dt.strftime('%H:%M')}")
    return "\n".join(lines)


def get_week_deadlines() -> str:
    """ددلاین‌های هفته."""
    conn = _connect()
    now = datetime.now()
    week_later = now + timedelta(days=7)

    rows = conn.execute(
        "SELECT title, deadline FROM assignments "
        "WHERE deadline >= ? AND deadline <= ? "
        "ORDER BY deadline LIMIT 15",
        (now.isoformat(), week_later.isoformat()),
    ).fetchall()
    conn.close()

    if not rows:
        return "📅 <b>ددلاین‌های هفته</b>\n\n✨ هیچ ددلاینی در هفته نیست!"

    lines = ["📅 <b>ددلاین‌های هفته</b>\n"]
    for r in rows:
        dt = datetime.fromisoformat(r["deadline"])
        days = (dt - now).days
        lines.append(f"  • {r['title'][:50]}")
        lines.append(f"    ⏰ {dt.strftime('%Y-%m-%d %H:%M')} ({days} روز)")
    return "\n".join(lines)


def get_quera_assignments() -> str:
    """تمرین‌های Quera."""
    conn = _connect()
    rows = conn.execute(
        "SELECT name, finish_time FROM quera_assignments "
        "ORDER BY finish_time LIMIT 15"
    ).fetchall()
    conn.close()

    if not rows:
        return "🎯 <b>تمرین‌های Quera</b>\n\n✨ هیچ تمرینی نیست!"

    lines = ["🎯 <b>تمرین‌های Quera</b>\n"]
    for r in rows:
        lines.append(f"  • {r['name'][:60]}")
        if r["finish_time"]:
            lines.append(f"    ⏰ {r['finish_time'][:16]}")
    return "\n".join(lines)


def get_recent_posts() -> str:
    """پست‌های اخیر."""
    conn = _connect()
    rows = conn.execute(
        "SELECT author, text, posted_at_jalali FROM posts "
        "ORDER BY posted_at DESC LIMIT 5"
    ).fetchall()
    conn.close()

    if not rows:
        return "📢 <b>پست‌های اخیر</b>\n\n✨ هیچ پستی نیست!"

    lines = ["📢 <b>پست‌های اخیر</b>\n"]
    for r in rows:
        text = r["text"][:100].replace("\n", " ")
        lines.append(f"  👤 <b>{r['author']}</b>")
        lines.append(f"    {text}...")
        lines.append("")
    return "\n".join(lines)


def get_stats() -> str:
    """آمار کلی."""
    conn = _connect()
    courses = conn.execute("SELECT COUNT(*) as n FROM courses").fetchone()["n"]
    assignments = conn.execute("SELECT COUNT(*) as n FROM assignments").fetchone()["n"]
    events = conn.execute("SELECT COUNT(*) as n FROM events").fetchone()["n"]
    quera = conn.execute("SELECT COUNT(*) as n FROM quera_assignments").fetchone()["n"]
    posts = conn.execute("SELECT COUNT(*) as n FROM posts").fetchone()["n"]
    members = conn.execute("SELECT COUNT(*) as n FROM members").fetchone()["n"]
    conn.close()

    return (
        "📊 <b>آمار کلی</b>\n\n"
        f"  📚 دروس: <b>{courses}</b>\n"
        f"  📋 تکالیف: <b>{assignments}</b>\n"
        f"  📅 رویدادها: <b>{events}</b>\n"
        f"  🎯 تمرین‌های Quera: <b>{quera}</b>\n"
        f"  📢 پست‌ها: <b>{posts}</b>\n"
        f"  👥 همکلاسی‌ها: <b>{members}</b>"
    )