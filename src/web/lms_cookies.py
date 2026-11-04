"""سریالایز / بازیابی کوکی‌های نشست LMS از کلاینت httpx."""

from __future__ import annotations

import json
from typing import Any


def dump_httpx_cookies(cookie_jar) -> str:
    """استخراج کوکی‌ها به JSON قابل ذخیره (سپس باید encrypt شود)."""
    items: list[dict[str, Any]] = []
    try:
        jar = cookie_jar.jar if hasattr(cookie_jar, "jar") else cookie_jar
        for cookie in jar:
            items.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain or "",
                    "path": cookie.path or "/",
                    "secure": bool(getattr(cookie, "secure", False)),
                }
            )
    except Exception:
        # fallback: dict-like
        try:
            for name, value in dict(cookie_jar).items():
                items.append(
                    {
                        "name": name,
                        "value": value,
                        "domain": "",
                        "path": "/",
                        "secure": False,
                    }
                )
        except Exception:
            return "[]"
    return json.dumps(items, ensure_ascii=False)


def load_httpx_cookies(client, cookies_json: str) -> int:
    """اعمال کوکی‌های ذخیره‌شده روی کلاینت. تعداد کوکی اعمال‌شده را برمی‌گرداند."""
    if not cookies_json:
        return 0
    try:
        items = json.loads(cookies_json)
    except json.JSONDecodeError:
        return 0
    if not isinstance(items, list):
        return 0

    count = 0
    jar = client.cookies if hasattr(client, "cookies") else client
    for item in items:
        name = item.get("name")
        value = item.get("value")
        if not name or value is None:
            continue
        domain = item.get("domain") or None
        path = item.get("path") or "/"
        try:
            if domain:
                jar.set(name, value, domain=domain, path=path)
            else:
                jar.set(name, value, path=path)
            count += 1
        except TypeError:
            # بعضی jarها signature متفاوت دارند
            try:
                jar.set(name, value)
                count += 1
            except Exception:
                pass
        except Exception:
            pass
    return count
