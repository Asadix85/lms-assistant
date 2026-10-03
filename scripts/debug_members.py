"""Debug: کشف ساختار همکلاسی‌ها در LMS."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def main():
    Path("data").mkdir(exist_ok=True)

    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()
        print(f"✅ Login. User ID: {assistant.user_id}\n")

        # یک درس انتخاب کن
        courses = assistant.get_all_courses()
        course = next(c for c in courses if c.domain == "lms4" and c.is_active)
        print(f"📚 درس: {course.name} (group_id={course.group_id})\n")

        # === تست ۱: صفحه wall درس ===
        url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
        r = assistant.client.get(url)
        print(f"GET {url} → {r.status_code} ({len(r.text)} bytes)\n")

        soup = BeautifulSoup(r.text, "lxml")

        # دنبال لینک‌های profile
        profile_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/profile/" in href:
                profile_links.add((href, a.get_text(strip=True)[:50]))

        print(f"=== لینک‌های profile ({len(profile_links)}) ===")
        for href, text in list(profile_links)[:20]:
            print(f"  {href} → {text}")

        # === تست ۲: endpointهای احتمالی ===
        print("\n=== تست endpointهای احتمالی ===")
        candidates = [
            f"https://lms4.ui.ac.ir/group/{course.group_id}/members",
            f"https://lms4.ui.ac.ir/group/member/{course.group_id}",
            f"https://lms4.ui.ac.ir/group/index/members/?group_id={course.group_id}",
            f"https://lms4.ui.ac.ir/groups/index/memberpack",
            f"https://lms4.ui.ac.ir/group/{course.group_id}/people",
        ]

        for url in candidates:
            try:
                r = assistant.client.get(url, timeout=15)
                print(f"\nGET {url}")
                print(f"  → {r.status_code} ({len(r.text)} bytes)")

                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    print(f"  body id: {body.get('id') if body else '?'}")

                    # ذخیره
                    fname = url.replace("https://", "").replace("/", "_").replace("?", "_")
                    Path(f"data/{fname}.html").write_text(r.text, encoding="utf-8")
                    print(f"  ذخیره: data/{fname}.html")

                    # دنبال profile links
                    profiles = soup.find_all("a", href=lambda h: h and "/profile/" in h)
                    print(f"  تعداد لینک profile: {len(profiles)}")
                    for p in profiles[:5]:
                        print(f"    {p['href']} → {p.get_text(strip=True)[:40]}")

            except Exception as e:
                print(f"\nGET {url} → خطا: {e}")


if __name__ == "__main__":
    main()