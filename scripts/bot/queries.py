"""کوئری‌های SQLite برای بات تلگرام — per-user با fallback تک‌کاربره."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("data/lms.db")


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"دیتابیس پیدا نشد: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_user_id(conn: sqlite3.Connection, user_id: str | None) -> str | None:
    """اگر user_id داده نشد، آخرین کاربر sync شده را برگردان. اگر هیچ نبود، None."""
    if user_id:
        row = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        return row["id"] if row else None
    row = conn.execute(
        "SELECT id FROM users WHERE is_active = 1 "
        "ORDER BY last_login_at DESC NULLS LAST LIMIT 1"
    ).fetchone()
    return row["id"] if row else None


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == column for r in rows)
    except sqlite3.OperationalError:
        return False


def get_today_assignments(user_id: str | None = None) -> str:
    """تکالیف امروز (deadline بین ۰۰:۰۰ امروز و ۰۰:۰۰ فردا)."""
    conn = _connect()
    uid = _resolve_user_id(conn, user_id)
    if not uid:
        conn.close()
        return "📋 <b>تکالیف امروز</b>\n\nکاربری یافت نشد."

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    rows = conn.execute(
        "SELECT title, deadline, course_name FROM assignments "
        "WHERE user_id = ? AND is_done = 0 "
        "  AND deadline IS NOT NULL AND deadline != '' "
        "  AND deadline >= ? AND deadline < ? "
        "ORDER BY deadline",
        (uid, today_start.isoformat(), today_end.isoformat()),
    ).fetchall()
    conn.close()

    if not rows:
        return "📋 <b>تکالیف امروز</b>\n\n✨ هیچ تکلیفی برای امروز نیست!"

    lines = ["📋 <b>تکالیف امروز</b>", f"🔢 <b>{len(rows)}</b> تکلیف", ""]
    for r in rows:
        dt = _safe_dt(r["deadline"])
        time_str = dt.strftime("⏰ %H:%M") if dt else ""
        course = f"📘 {r['course_name']}\n" if r["course_name"] else ""
        lines.append(f"  • {_cut(r['title'], 60)}")
        if course:
            lines.append(f"    {course.strip()}")
        if time_str:
            lines.append(f"    {time_str}")
    return "\n".join(lines)


def get_week_deadlines(user_id: str | None = None) -> str:
    """ددلاین‌های ۷ روز آینده."""
    conn = _connect()
    uid = _resolve_user_id(conn, user_id)
    if not uid:
        conn.close()
        return "📅 <b>ددلاین‌های هفته</b>\n\nکاربری یافت نشد."

    now = datetime.now()
    week_later = now + timedelta(days=7)

    rows = conn.execute(
        "SELECT title, deadline, course_name FROM assignments "
        "WHERE user_id = ? AND is_done = 0 "
        "  AND deadline IS NOT NULL AND deadline != '' "
        "  AND deadline >= ? AND deadline <= ? "
        "ORDER BY deadline LIMIT 15",
        (uid, now.isoformat(), week_later.isoformat()),
    ).fetchall()
    conn.close()

    if not rows:
        return "📅 <b>ددلاین‌های هفته</b>\n\n✨ هیچ ددلاینی در هفتهٔ آینده نیست!"

    lines = ["📅 <b>ددلاین‌های هفتهٔ آینده</b>", f"🔢 <b>{len(rows)}</b> ددلاین", ""]
    for r in rows:
        dt = _safe_dt(r["deadline"])
        if not dt:
            continue
        days = (dt - now).days
        when = "امروز" if days == 0 else f"{days} روز دیگر"
        lines.append(f"  • {_cut(r['title'], 55)}")
        lines.append(f"    🗓 {dt.strftime('%Y-%m-%d %H:%M')} ({when})")
        if r["course_name"]:
            lines.append(f"    📘 {r['course_name']}")
        lines.append("")
    return "\n".join(lines)


def get_quera_assignments(user_id: str | None = None) -> str:
    """تمرین‌های Quera."""
    conn = _connect()
    uid = _resolve_user_id(conn, user_id)
    if not uid:
        conn.close()
        return "🎯 <b>تمرین‌های Quera</b>\n\nکاربری یافت نشد."

    if not _has_column(conn, "quera_assignments", "id"):
        conn.close()
        return "🎯 <b>تمرین‌های Quera</b>\n\nجدول Quera ساخته نشده. یک بار sync بزن."

    rows = conn.execute(
        "SELECT name, finish_time, course_name, submitted_count, problems_count "
        "FROM quera_assignments WHERE user_id = ? "
        "ORDER BY COALESCE(finish_time, '9999-12-31') LIMIT 15",
        (uid,),
    ).fetchall()
    conn.close()

    if not rows:
        return "🎯 <b>تمرین‌های Quera</b>\n\n✨ هیچ تمرینی نیست."

    lines = ["🎯 <b>تمرین‌های Quera</b>", f"🔢 <b>{len(rows)}</b> تمرین", ""]
    for r in rows:
        lines.append(f"  • {_cut(r['name'], 60)}")
        if r["course_name"]:
            lines.append(f"    📘 {r['course_name']}")
        if r["finish_time"]:
            lines.append(f"    ⏰ {r['finish_time'][:16]}")
        if r["problems_count"]:
            done = r["submitted_count"] or 0
            lines.append(f"    ✅ {done}/{r['problems_count']} حل شده")
        lines.append("")
    return "\n".join(lines)


def get_recent_posts(user_id: str | None = None) -> str:
    """۵ پست آخر وال."""
    conn = _connect()
    uid = _resolve_user_id(conn, user_id)
    if not uid:
        conn.close()
        return "📢 <b>پست‌های اخیر</b>\n\nکاربری یافت نشد."

    cols = "id, author, text, posted_at_jalali, course_name"
    try:
        rows = conn.execute(
            f"SELECT {cols} FROM posts WHERE user_id = ? "
            "ORDER BY posted_at DESC LIMIT 5",
            (uid,),
        ).fetchall()
    except sqlite3.OperationalError:
        conn.close()
        return "📢 <b>پست‌های اخیر</b>\n\nجدول posts در دسترس نیست."
    conn.close()

    if not rows:
        return "📢 <b>پست‌های اخیر</b>\n\n✨ هیچ پستی نیست."

    lines = ["📢 <b>پست‌های اخیر</b>", ""]
    for r in rows:
        text = (r["text"] or "")[:120].replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")
        lines.append(f"  👤 <b>{_esc(r['author'] or '—')}</b>")
        if r["course_name"]:
            lines.append(f"    📘 {_esc(r['course_name'])}")
        lines.append(f"    {text}{'…' if len(r['text'] or '') > 120 else ''}")
        if r["posted_at_jalali"]:
            lines.append(f"    🕒 {_esc(r['posted_at_jalali'])}")
        lines.append("")
    return "\n".join(lines)


def get_stats(user_id: str | None = None) -> str:
    """آمار کلی — فقط برای کاربر مشخص."""
    conn = _connect()
    uid = _resolve_user_id(conn, user_id)
    if not uid:
        conn.close()
        return "📊 <b>آمار</b>\n\nکاربری یافت نشد."

    def _count(table: str, where: str = "") -> int:
        try:
            sql = f"SELECT COUNT(*) AS n FROM {table} WHERE user_id = ?"
            if where:
                sql += f" AND {where}"
            row = conn.execute(sql, (uid,)).fetchone()
            return row["n"] if row else 0
        except sqlite3.OperationalError:
            return 0

    stats = {
        "courses": _count("courses"),
        "assignments": _count("assignments"),
        "open": _count("assignments", "is_done = 0"),
        "overdue": _count(
            "assignments",
            f"is_done = 0 AND deadline < '{datetime.now().isoformat()}'",
        ),
        "events": _count("events"),
        "posts": _count("posts"),
        "unread_posts": _count("posts", "is_new = 1"),
        "contents": _count("contents"),
        "quera": _count("quera_assignments") if _has_column(conn, "quera_assignments", "user_id") else 0,
    }
    conn.close()

    return (
        "📊 <b>آمار کلی</b>\n\n"
        f"  📚 دروس: <b>{stats['courses']}</b>\n"
        f"  📋 تکالیف: <b>{stats['assignments']}</b> "
        f"(باز: <b>{stats['open']}</b> · عقب‌افتاده: <b>{stats['overdue']}</b>)\n"
        f"  📅 رویدادها: <b>{stats['events']}</b>\n"
        f"  📢 پست‌ها: <b>{stats['posts']}</b> (نخوانده: <b>{stats['unread_posts']}</b>)\n"
        f"  📁 محتواها: <b>{stats['contents']}</b>\n"
        f"  🎯 کوئرا: <b>{stats['quera']}</b>"
    )


def _safe_dt(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except (ValueError, TypeError):
        return None


def _cut(s: str | None, n: int) -> str:
    s = (s or "").strip()
    return _esc(s) if len(s) <= n else _esc(s[:n]) + "…"


def _esc(s: str | None) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")