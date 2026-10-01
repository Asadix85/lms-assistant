"""تست: آیا بعد از nodeg، session lms3 ست می‌شود؟"""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


def main():
    # Login به lms4
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir", timeout=30) as client:
        auth = LMSAuth(client)
        auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"])
        print(f"✅ Logged in to lms4. User ID: {auth.user_id}\n")

        # ۱. کوکی‌های فعلی
        print("=== کوکی‌ها قبل از nodeg ===")
        for cookie in client.cookies.jar:
            print(f"  {cookie.name} @ {cookie.domain}")

        # ۲. دریافت لینک nodeg
        r = client.get("/pages/nodeclass")
        soup = BeautifulSoup(r.text, "lxml")
        lms3_url = None
        for a in soup.find_all("a", href=True):
            if "lms3.ui.ac.ir/nodeg/" in a["href"]:
                lms3_url = a["href"]
                break

        if not lms3_url:
            print("❌ لینک lms3 پیدا نشد")
            return

        # ۳. GET nodeg
        print(f"\n=== GET nodeg ===")
        r = client.get(lms3_url, timeout=30)
        print(f"Status: {r.status_code}")
        print(f"طول: {len(r.text)}")

        # ۴. کوکی‌های بعد از nodeg
        print("\n=== کوکی‌ها بعد از nodeg ===")
        for cookie in client.cookies.jar:
            print(f"  {cookie.name} @ {cookie.domain}")

        # ۵. صفحه‌ی nodeg چه چیزی است؟
        soup_nodeg = BeautifulSoup(r.text, "lxml")
        body = soup_nodeg.find("body")
        print(f"\nbody id: {body.get('id')}")

        # ۶. لینک‌های داخل صفحه nodeg
        print("\n=== لینک‌های داخل nodeg ===")
        for a in soup_nodeg.find_all("a", href=True)[:20]:
            href = a["href"]
            text = a.get_text(strip=True)[:50]
            if href and not href.startswith("#"):
                print(f"  {href[:80]} → {text}")

        # ۷. حالا تلاش کن به /pages/nodemain در lms3 بروی
        print("\n=== تست: GET lms3/pages/nodemain ===")
        r2 = client.get("https://lms3.ui.ac.ir/pages/nodemain", timeout=30)
        print(f"Status: {r2.status_code}")
        print(f"URL نهایی: {r2.url}")
        print(f"طول: {len(r2.text)}")
        if "user_form_login" in r2.text:
            print("❌ هنوز فرم لاگین است")
        else:
            print("✅ وارد lms3 شده‌ایم!")

        # ۸. تلاش برای /pages/nodeclass در lms3
        print("\n=== تست: GET lms3/pages/nodeclass ===")
        r3 = client.get("https://lms3.ui.ac.ir/pages/nodeclass", timeout=30)
        print(f"Status: {r3.status_code}")
        print(f"طول: {len(r3.text)}")
        if r3.status_code == 200:
            soup3 = BeautifulSoup(r3.text, "lxml")
            courses = soup3.find_all("div", class_="classwig")
            print(f"تعداد درس‌ها در lms3: {len(courses)}")
            Path("data").mkdir(exist_ok=True)
            Path("data/lms3_nodeclass.html").write_text(r3.text, encoding="utf-8")
            print("ذخیره شد: data/lms3_nodeclass.html")


if __name__ == "__main__":
    main()