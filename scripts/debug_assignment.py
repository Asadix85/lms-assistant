"""Debug: کشف ساختار assignment (تکالیف)."""

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

        courses = assistant.get_all_courses()

        # === کشف assignment در همه دروس ===
        all_assignments = []

        for course in courses:
            if not course.is_active:
                continue

            print(f"📚 {course.name} ({course.domain})")

            # URL درس
            if course.domain == "lms4":
                url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
            else:
                # lms3 - از nodeg
                if not course.nodeg_url:
                    continue
                # از nodeclass لمس 3 استفاده کن (توکن داره)
                url = f"https://lms3.ui.ac.ir/group/{course.group_id}"

            r = assistant.client.get(url)
            if r.status_code != 200:
                print(f"  ❌ {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "lxml")

            # پیدا کردن لینک‌های assignment
            assignments = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/assignment/" in href:
                    # استخراج assignment_id
                    import re
                    match = re.search(r"/assignment/\w+/(\d+)", href)
                    if match:
                        aid = match.group(1)
                        text = a.get_text(strip=True)
                        assignments.append((aid, href, text))

            if assignments:
                print(f"  🎯 {len(assignments)} لینک assignment پیدا شد")
                for aid, href, text in assignments:
                    print(f"     ID={aid}: {href[:60]} → {text[:40]}")
                    all_assignments.append((course.group_id, course.domain, aid))
            else:
                print(f"  ⚠️ هیچ assignment پیدا نشد")

        # === کشف ساختار یک assignment ===
        if all_assignments:
            print("\n" + "=" * 70)
            print(f"کشف ساختار assignment (اولین: {all_assignments[0]})")
            print("=" * 70)

            course_id, domain, aid = all_assignments[0]

            # چند endpoint احتمالی
            candidates = [
                f"https://{domain}.ui.ac.ir/assignment/view/{aid}",
                f"https://{domain}.ui.ac.ir/assignment/viewresponse/{aid}",
                f"https://{domain}.ui.ac.ir/assignment/sendreplay/{aid}",
                f"https://lms4.ui.ac.ir/assignment/view/{aid}",
            ]

            for url in candidates:
                try:
                    r = assistant.client.get(url, timeout=20)
                    print(f"\n{url}")
                    print(f"  → {r.status_code} ({len(r.text)} bytes)")

                    if r.status_code == 200 and len(r.text) > 5000:
                        soup = BeautifulSoup(r.text, "lxml")
                        body = soup.find("body")
                        print(f"  body id: {body.get('id') if body else '?'}")

                        # ذخیره
                        fname = url.replace("https://", "").replace("/", "_").replace("?", "_")
                        Path(f"data/{fname}.html").write_text(r.text, encoding="utf-8")
                        print(f"  ذخیره: data/{fname}.html")

                        # عنوان
                        title = soup.find(["h1", "h2", "h3"])
                        if title:
                            print(f"  عنوان: {title.get_text(strip=True)[:80]}")

                        # کلمات کلیدی
                        keywords = ["مهلت", "تاریخ", "deadline", "due", "نمره", "پاسخ"]
                        for kw in keywords:
                            count = r.text.count(kw)
                            if count > 0:
                                print(f"  '{kw}': {count} بار")

                except Exception as e:
                    print(f"{url} → خطا: {e}")


if __name__ == "__main__":
    main()