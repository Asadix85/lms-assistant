"""پیام‌های قابل‌فهم برای خطا و وضعیت sync."""

from __future__ import annotations


def humanize_sync_error(raw: str | None) -> str:
    if not raw:
        return "خطای نامشخص در همگام‌سازی"
    text = str(raw).strip()
    low = text.lower()

    rules: list[tuple[tuple[str, ...], str]] = [
        (
            ("منقضی", "session", "401", "403", "login به lms ناموفق", "وارد شوید"),
            "نشست LMS منقضی یا نامعتبر است — یک‌بار از منوی حساب خارج و دوباره وارد شوید.",
        ),
        (
            ("نام کاربری یا رمز", "credentials", "auth"),
            "اعتبارنامه LMS رد شد — دوباره با رمز درست وارد شوید.",
        ),
        (
            ("timeout", "timed out", "زمان"),
            "پاسخ LMS طول کشید (timeout). کمی بعد دوباره همگام‌سازی کنید.",
        ),
        (
            ("connection", "connect", "network", "ارتباط", "dns", "refused"),
            "ارتباط با سرور LMS برقرار نشد. اینترنت یا دسترسی به LMS را بررسی کنید.",
        ),
        (
            ("quera",),
            "همگام‌سازی کوئرا مشکل داشت؛ داده LMS ممکن است به‌روز باشد.",
        ),
        (
            ("permission", "دسترسی"),
            "دسترسی کافی برای همگام‌سازی نیست — دوباره وارد شوید.",
        ),
    ]
    for keys, msg in rules:
        if any(k in low or k in text for k in keys):
            return msg
    # کوتاه‌سازی پیام فنی خیلی بلند
    if len(text) > 180:
        return text[:177] + "…"
    return text


def format_last_sync(
    *,
    ok: bool | None,
    at: str | None,
    summary: str | None,
    error: str | None,
) -> dict:
    human_error = humanize_sync_error(error) if error else None
    if ok is True:
        status = "success"
        title = "آخرین همگام‌سازی موفق"
        detail = summary or "همه چیز به‌روز است"
    elif ok is False:
        status = "error"
        title = "آخرین همگام‌سازی ناموفق"
        detail = human_error or summary or "خطا"
    else:
        status = "never"
        title = "هنوز همگام‌سازی نشده"
        detail = "با دکمه «همگام‌سازی» داده را از LMS بگیرید"
    return {
        "status": status,
        "ok": ok,
        "at": at,
        "summary": summary,
        "error": error,
        "error_human": human_error,
        "title": title,
        "detail": detail,
    }
