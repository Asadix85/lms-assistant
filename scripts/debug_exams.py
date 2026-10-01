"""Debug: کشف اینکه آزمون‌ها کجا هستند."""

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

        # === تست ۱: دنبال Hequestion یا آزمون در صفحه درس ===
        print("=== ۱. بررسی صفحه درس (wall) ===")
        for course in courses[:2]:  # ۲ درس اول
            if not course.is_active:
                continue

            print(f"\n📚 {course.name} ({course.domain})")

            # URL صفحه درس
            if course.domain == "lms4":
                url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
            else:
                url = course.url  # nodeg_url

            r = assistant.client.get(url)
            if r.status_code != 200:
                print(f"  ❌ {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "lxml")

            # جستجوی کلمات کلیدی
            keywords = ["آزمون", "امتحان", "کوییز", "quiz", "exam",
                        "تکلیف", "تمرین", "پروژه", "مهلت", "ددلاین",
                        "deadline", "assignment", "question", "hequestion"]
            found = {}
            for kw in keywords:
                count = r.text.lower().count(kw.lower())
                if count > 0:
                    found[kw] = count

            print(f"  کلمات کلیدی: {found}")

            # دنبال لینک‌های exam-like
            print(f"  لینک‌های exam-like:")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(x in href.lower() for x in
                       ["/question", "exam", "quiz", "azmoon", "/activity/"]):
                    print(f"    {href[:80]} → {a.get_text(strip=True)[:50]}")

        # === تست ۲: endpointهای احتمالی آزمون ===
        print("\n\n=== ۲. تست endpointهای احتمالی آزمون ===")
        candidate_urls = [
            "https://lms4.ui.ac.ir/question-box",
            "https://lms4.ui.ac.ir/question-view",
            "https://lms4.ui.ac.ir/azmoon",
            "https://lms4.ui.ac.ir/exam",
            "https://lms4.ui.ac.ir/pages/exam",
            "https://lms4.ui.ac.ir/activity/notifications",
            "https://lms4.ui.ac.ir/pages/calendar",
        ]
        for url in candidate_urls:
            try:
                r = assistant.client.get(url, timeout=15)
                print(f"  {url} → {r.status_code} ({len(r.text)} bytes)")
                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    print(f"    body id: {body.get('id') if body else '?'}")
                    # ذخیره
                    fname = url.replace("https://", "").replace("/", "_")
                    Path(f"data/{fname}.html").write_text(r.text, encoding="utf-8")
            except Exception as e:
                print(f"  {url} → خطا: {type(e).__name__}: {e}")

        # === تست ۳: پیام‌ها و اعلان‌ها ===
        print("\n\n=== ۳. پیام‌ها و اعلان‌ها ===")
        for url in [
            "https://lms4.ui.ac.ir/activity/notifications",
            "https://lms4.ui.ac.ir/messages/inbox",
        ]:
            try:
                r = assistant.client.get(url, timeout=15)
                print(f"  {url} → {r.status_code} ({len(r.text)} bytes)")
                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    print(f"    body id: {body.get('id') if body else '?'}")
                    # ذخیره
                    fname = url.replace("https://", "").replace("/", "_")
                    Path(f"data/{fname}.html").write_text(r.text, encoding="utf-8")
            except Exception as e:
                print(f"  {url} → خطا: {e}")


if __name__ == "__main__":
    main()