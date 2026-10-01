"""Debug: کشف ساختار listofcontent."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


def main():
    # درس ساختمان داده در lms4 (که 11 PDF داشت)
    COURSE_ID = "134345"

    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        # Login
        auth = LMSAuth(client)
        if not auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"]):
            print("❌ Login failed")
            return

        # GET listofcontent
        url = f"/group/index/listofcontent/?group_id={COURSE_ID}"
        r = client.get(url)
        print(f"GET {url} → {r.status_code} ({len(r.text)} bytes)")

        # ذخیره
        Path("data").mkdir(exist_ok=True)
        Path(f"data/listofcontent_{COURSE_ID}.html").write_text(r.text, encoding="utf-8")
        print(f"ذخیره شد: data/listofcontent_{COURSE_ID}.html")

        # تحلیل
        soup = BeautifulSoup(r.text, "lxml")

        # body id
        body = soup.find("body")
        print(f"\nbody id: {body.get('id')}")

        # تعداد لینک‌های /file/, .pdf, .zip
        print("\n=== لینک‌های محتوا ===")
        patterns = ["/file/", ".pdf", ".zip", ".docx", ".pptx", ".mp4", "pluginfile", "download"]
        found = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            for p in patterns:
                if p in href.lower():
                    found.setdefault(p, []).append((href, a.get_text(strip=True)[:60]))

        for p, items in found.items():
            print(f"\n=== {p} ({len(items)} مورد) ===")
            for href, text in items[:5]:
                print(f"  {href[:100]}")
                print(f"    → {text}")

        # همه لینک‌های داخل main content
        print("\n=== همه لینک‌ها در global_content ===")
        content = soup.find(id="global_content")
        if content:
            links = content.find_all("a", href=True)
            print(f"تعداد: {len(links)}")
            for a in links[:20]:
                href = a["href"]
                text = a.get_text(strip=True)[:60]
                print(f"  {href[:100]}")
                print(f"    → {text}")


if __name__ == "__main__":
    main()