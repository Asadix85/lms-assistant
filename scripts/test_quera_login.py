"""تست لاگین کوئرا با تاخیر (برای جلوگیری از Rate Limit)."""

import time
from loguru import logger
from src.core.quera_client import QueraHttpClient

# 👇 اطلاعات لاگین خود را اینجا وارد کنید
IDENTIFIER = "4043613005"
PASSWORD = "580813850928Ma"

def main():
    logger.info("شروع تست لاگین کوئرا (با تاخیر)...")

    client = QueraHttpClient()

    # ۱. دریافت CSRF
    logger.info("۱. دریافت CSRF...")
    login_page = client.get("/accounts/login")

    csrf_token = None
    for name in ["csrftoken", "csrf_token"]:
        csrf_token = client.cookies.get(name)
        if csrf_token:
            break

    if not csrf_token:
        import re
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
        if match:
            csrf_token = match.group(1)

    if not csrf_token:
        logger.error("❌ CSRF پیدا نشد.")
        return

    logger.success(f"✅ CSRF: {csrf_token[:20]}...")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-CSRFToken": csrf_token,
        "Referer": "https://quera.org/accounts/login",
        "Origin": "https://quera.org",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # ۲. ساختارهای مختلف با تاخیر ۵ ثانیه
    payloads = [
        {"identifier": IDENTIFIER},
        {"email": IDENTIFIER},
        {"username": IDENTIFIER},
        {"identifier": IDENTIFIER, "preferred_process": "password"},
        {"email": IDENTIFIER, "preferred_process": "password"},
    ]

    for i, payload in enumerate(payloads):
        if i > 0:
            logger.info("⏳ صبر ۵ ثانیه برای جلوگیری از Rate Limit...")
            time.sleep(5)

        logger.info(f"تلاش {i+1}: {payload}")
        try:
            r = client.post("/accounts/api/login/", json=payload, headers=headers)
            logger.info(f"پاسخ: {r.status_code} - {r.text[:200]}")

            if r.status_code == 200:
                logger.success(f"✅✅ موفق! payload: {payload}")
                logger.success(f"پاسخ کامل: {r.json()}")
                return
            elif r.status_code == 429:
                logger.warning("⏳ بلاک شدیم. ۱۰ ثانیه صبر می‌کنیم...")
                time.sleep(10)
        except Exception as e:
            logger.warning(f"خطا: {e}")

    logger.error("❌ هیچ‌کدام از ساختارها کار نکرد.")

if __name__ == "__main__":
    main()