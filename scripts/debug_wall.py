"""Debug: کشف ساختار wall درس (پیام‌های استاد)."""

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
        # یک درس lms4 با wall فعال
        course = next(c for c in courses if c.domain == "lms4" and c.is_active)
        print(f"📚 درس: {course.name} (group_id={course.group_id})\n")

        # GET wall درس
        url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
        r = assistant.client.get(url)
        print(f"GET {url} → {r.status_code} ({len(r.text)} bytes)\n")

        Path(f"data/wall_{course.group_id}.html").write_text(r.text, encoding="utf-8")
        print(f"ذخیره: data/wall_{course.group_id}.html\n")

        soup = BeautifulSoup(r.text, "lxml")

        # === کشف ساختار wall ===
        print("=" * 70)
        print("۱. Feed Items (پیام‌های wall)")
        print("=" * 70)

        feed_items = soup.find_all("li", class_=lambda x: x and "feed" in str(x).lower())
        print(f"تعداد feed items: {len(feed_items)}\n")

        for i, item in enumerate(feed_items[:5], 1):
            print(f"--- Feed Item {i} ---")
            text = item.get_text(separator=" ", strip=True)[:300]
            print(f"متن: {text}\n")

            # لینک‌های داخل
            for a in item.find_all("a", href=True)[:5]:
                print(f"  لینک: {a['href'][:80]} → {a.get_text(strip=True)[:50]}")

            # دنبال ددلاین یا تاریخ
            import re
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
            if dates:
                print(f"  ⚠️ تاریخ پیدا شد: {dates}")

            print()

        # === کشف Hequestion (آزمون/سوال) ===
        print("=" * 70)
        print("۲. Hequestion (آزمون/سوال)")
        print("=" * 70)

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "question" in href.lower() or "hequestion" in href.lower():
                print(f"  {href[:100]}")
                print(f"    → {a.get_text(strip=True)[:80]}")

        # === کشف تکالیف ===
        print("\n" + "=" * 70)
        print("۳. دنبال تکالیف (assignment, تمرین, پروژه)")
        print("=" * 70)

        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.get_text(strip=True)
            if any(kw in href or kw in text.lower() for kw in
                   ["assignment", "homework", "task", "تمرین", "تکلیف", "پروژه"]):
                print(f"  {a['href'][:100]}")
                print(f"    → {text[:80]}")

        # === کشف تاریخ‌ها و ددلاین‌ها ===
        print("\n" + "=" * 70)
        print("۴. دنبال ددلاین (مهلت، deadline، due)")
        print("=" * 70)

        html_lower = r.text.lower()
        for kw in ["مهلت", "deadline", "due", "ددلاین", "تحویل"]:
            count = html_lower.count(kw)
            if count > 0:
                print(f"  '{kw}': {count} بار")

                # پیدا کردن متن اطراف
                import re
                pattern = re.compile(rf".{{50}}{kw}.{{100}}", re.IGNORECASE)
                matches = pattern.findall(r.text)
                for m in matches[:3]:
                    clean = BeautifulSoup(m, "lxml").get_text(strip=True)
                    print(f"    → ...{clean}...")


if __name__ == "__main__":
    main()