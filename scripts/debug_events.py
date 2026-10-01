"""Debug: کشف رویدادها (تقویم + اعلان‌ها)."""

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

        # === ۱. تقویم ===
        print("=" * 60)
        print("📅 تقویم - /pages/calendar")
        print("=" * 60)

        r = assistant.client.get("https://lms4.ui.ac.ir/pages/calendar")
        print(f"Status: {r.status_code}, طول: {len(r.text)}\n")

        soup = BeautifulSoup(r.text, "lxml")

        # دنبال رویدادها
        print("=== رویدادها (جدول یا لیست) ===")
        tables = soup.find_all("table")
        for i, table in enumerate(tables):
            rows = table.find_all("tr")
            print(f"\nجدول {i+1}: {len(rows)} سطر")
            for row in rows[:10]:
                cells = [td.get_text(strip=True)[:40] for td in row.find_all(["td", "th"])]
                if any(cells):
                    print(f"  {cells}")

        # لینک‌ها
        print("\n=== لینک‌های مهم ===")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(x in href for x in ["jaam", "event", "exam", "event/", "/pages/"]):
                text = a.get_text(strip=True)[:50]
                if text:
                    print(f"  {href[:80]} → {text}")

        # === ۲. اعلان‌ها ===
        print("\n" + "=" * 60)
        print("🔔 اعلان‌ها - /activity/notifications")
        print("=" * 60)

        r2 = assistant.client.get("https://lms4.ui.ac.ir/activity/notifications")
        print(f"Status: {r2.status_code}, طول: {len(r2.text)}\n")

        soup2 = BeautifulSoup(r2.text, "lxml")

        # دنبال آیتم‌های اعلان
        feed_items = soup2.find_all("li", class_=lambda x: x and "feed" in str(x).lower())
        print(f"تعداد feed items: {len(feed_items)}")

        for item in feed_items[:10]:
            text = item.get_text(strip=True)[:100]
            if text:
                print(f"  • {text}")

        # دنبال کلمات کلیدی در اعلان‌ها
        print("\n=== کلمات کلیدی در اعلان‌ها ===")
        for kw in ["آزمون", "امتحان", "تکلیف", "تمرین", "مهلت", "جلسه"]:
            count = r2.text.count(kw)
            if count > 0:
                print(f"  '{kw}': {count}")

        # === ۳. wall درس lms4 (مدار) — دنبال post های Hequestion ===
        print("\n" + "=" * 60)
        print("📝 wall درس lms4 (مدارهای الکتریکی)")
        print("=" * 60)

        r3 = assistant.client.get("https://lms4.ui.ac.ir/group/139710")
        soup3 = BeautifulSoup(r3.text, "lxml")

        # دنبال لینک‌های question-view
        print("=== لینک‌های question ===")
        for a in soup3.find_all("a", href=True):
            href = a["href"]
            if "question" in href.lower():
                text = a.get_text(strip=True)[:80]
                print(f"  {href[:80]}")
                print(f"    → {text}")

        # دنبال feed items
        print("\n=== feed items در wall ===")
        feed_items3 = soup3.find_all("li", class_=lambda x: x and "feed" in str(x).lower())
        print(f"تعداد: {len(feed_items3)}")
        for item in feed_items3[:5]:
            text = item.get_text(strip=True)[:150]
            if text:
                print(f"  • {text}")


if __name__ == "__main__":
    main()