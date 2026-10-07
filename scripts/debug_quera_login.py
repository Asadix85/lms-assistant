"""Debug Quera login page."""

import re
from pathlib import Path

import httpx


def main() -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fa-IR,fa;q=0.9",
    }

    r = httpx.get(
        "https://quera.org/accounts/login",
        follow_redirects=True,
        headers=headers,
    )

    print("=" * 50)
    print(f"Status: {r.status_code}")
    print(f"URL: {r.url}")
    print(f"Size: {len(r.text)} کاراکتر")
    print("=" * 50)

    # === چک الگوها ===
    patterns = {
        "csrfmiddlewaretoken (name)": r'name="csrfmiddlewaretoken"',
        "csrf (any)": r"csrf",
        "csrftoken (cookie)": r"csrftoken",
        "login form": r'name="login"',
        "password form": r'name="password"',
        "form tag": r"<form",
        "input tag": r"<input",
        "__NEXT_DATA__": r"__NEXT_DATA__",
        "react": r"react",
    }

    print("\n🔍 الگوها:")
    for name, pattern in patterns.items():
        count = len(re.findall(pattern, r.text, re.IGNORECASE))
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name}: {count}")

    # === کوکی‌ها ===
    print("\n🍪 Cookies:")
    for name, value in r.cookies.items():
        # فقط اسم رو نشون بده، نه مقدار
        print(f"  - {name} (طول: {len(value)})")

    # === ذخیره HTML ===
    out = Path("debug_quera_login.html")
    out.write_text(r.text, encoding="utf-8")
    print(f"\n💾 ذخیره شد: {out}")

    # === نمونه از body ===
    print("\n📄 نمونه از HTML (اولین ۵۰۰ کاراکتر body):")
    # پیدا کردن body tag
    body_match = re.search(r"<body[^>]*>(.*)", r.text, re.DOTALL)
    if body_match:
        body = body_match.group(1)[:500]
        print(body)
    else:
        print("body tag پیدا نشد")


if __name__ == "__main__":
    main()