"""ساخت تقویم ICS از تکالیف و رویدادهای کاربر."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable


def _esc(text: str) -> str:
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def _fmt_utc(dt: datetime) -> str:
    # اگر naive است همان را به‌عنوان local می‌نویسیم (فرمت floating)
    return dt.strftime("%Y%m%dT%H%M%S")


def _fold(line: str) -> str:
    # RFC 5545 line folding ~75 octets — ساده
    if len(line) <= 73:
        return line
    parts = [line[:73]]
    rest = line[73:]
    while rest:
        parts.append(" " + rest[:72])
        rest = rest[72:]
    return "\r\n".join(parts)


def build_ics(
    *,
    assignments: Iterable,
    events: Iterable,
    calendar_name: str = "LMS Assistant",
) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LMS Assistant//FA//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_esc(calendar_name)}",
    ]

    for a in assignments:
        deadline = getattr(a, "deadline", None)
        if not deadline:
            continue
        title = getattr(a, "title", "تکلیف") or "تکلیف"
        uid = f"assignment-{getattr(a, 'id', 'x')}@lms-assistant"
        desc = getattr(a, "description", "") or ""
        # یادآوری: رویداد یک‌ساعته منتهی به ددلاین
        start = deadline - timedelta(hours=1)
        if start >= deadline:
            start = deadline - timedelta(minutes=30)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{_fmt_utc(datetime.utcnow())}",
                f"DTSTART:{_fmt_utc(start)}",
                f"DTEND:{_fmt_utc(deadline)}",
                f"SUMMARY:{_esc('تکلیف: ' + title)}",
                f"DESCRIPTION:{_esc(desc[:500])}",
                "END:VEVENT",
            ]
        )

    for e in events:
        start = getattr(e, "start_at", None)
        if not start:
            continue
        title = getattr(e, "title", "رویداد") or "رویداد"
        uid = f"event-{getattr(e, 'id', 'x')}@lms-assistant"
        end = start + timedelta(hours=1)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{_fmt_utc(datetime.utcnow())}",
                f"DTSTART:{_fmt_utc(start)}",
                f"DTEND:{_fmt_utc(end)}",
                f"SUMMARY:{_esc(title)}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in lines) + "\r\n"
