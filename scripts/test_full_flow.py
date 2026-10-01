"""تست کامل: login + nodeg + دسترسی به lms3 + لیست درس‌های lms3."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


def main():
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir", timeout=30) as client:
        # ۱. Login
        auth = LMSAuth(client)
        auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"])
        print(f"✅ Login lms4. User ID: {auth.user_id}\n")

        # ۲. nodeclass lms4
        r = client.get("/pages/nodeclass")
        soup = BeautifulSoup(r.text, "lxml")

        # پیدا کردن لینک nodeg
        nodeg_urls = []
        for a in soup.find_all("a", href=True):
            if "/nodeg/" in a["href"]:
                nodeg_urls.append((a["href"], a.get_text(strip=True)))

        print(f"🔗 تعداد لینک nodeg: {len(nodeg_urls)}")
        for url, text in nodeg_urls[:5]:
            # redact token
            parts = url.split("/")
            redacted = f"{parts[0]}//{parts[2]}/nodeg/<TOKEN>/{parts[4]}/{parts[5]}"
            print(f"  {redacted} → {text[:40]}")
        print()

        # ۳. GET اولین nodeg (برای ست کردن session lms3)
        if nodeg_urls:
            first_nodeg = nodeg_urls[0][0]
            print(f"🧪 GET اولین nodeg...")
            r2 = client.get(first_nodeg)
            print(f"   Status: {r2.status_code}\n")

        # ۴. حالا چک کنیم session lms3
        print(f"🍪 کوکی‌ها:")
        for cookie in client.cookies.jar:
            print(f"   {cookie.name} @ {cookie.domain}")
        print()

        # ۵. لیست درس‌های lms3
        print(f"📚 لیست درس‌های lms3:")
        r3 = client.get("https://lms3.ui.ac.ir/pages/nodeclass", timeout=30)
        if r3.status_code == 200:
            soup3 = BeautifulSoup(r3.text, "lxml")
            courses3 = soup3.find_all("div", class_="classwig")
            print(f"   تعداد: {len(courses3)}")
            for c in courses3[:5]:
                h2 = c.find("h2", class_="classtitle")
                master = c.find("div", class_="mastertitle")
                if h2:
                    name = h2.get_text(strip=True)
                    teacher = master.get_text(strip=True) if master else "?"
                    print(f"   • {name} ({teacher})")
        else:
            print(f"   ❌ Status: {r3.status_code}")


if __name__ == "__main__":
    main()