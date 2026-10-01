"""Debug: کشف ساختار jaam (آزمون‌ها)."""

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

        # ۱. تست jaam/unbound/index (همه جلسات)
        print("=== jaam/unbound/index ===")
        for domain in ["lms3", "lms4", "lms5"]:
            url = f"https://{domain}.ui.ac.ir/jaam/unbound/index"
            try:
                r = assistant.client.get(url, timeout=30)
                print(f"  {url}")
                print(f"    → {r.status_code} ({len(r.text)} bytes)")

                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    print(f"    body id: {body.get('id') if body else '?'}")

                    # ذخیره
                    path = Path(f"data/jaam_unbound_{domain}.html")
                    path.write_text(r.text, encoding="utf-8")
                    print(f"    ذخیره: {path}")

                    # لینک‌های jaam/rooms
                    rooms = []
                    for a in soup.find_all("a", href=True):
                        if "/jaam/" in a["href"]:
                            rooms.append((a["href"], a.get_text(strip=True)[:50]))

                    if rooms:
                        print(f"    لینک‌های jaam: {len(rooms)}")
                        for href, text in rooms[:10]:
                            print(f"      {href} → {text}")
                print()
            except Exception as e:
                print(f"  {url} → خطا: {type(e).__name__}: {e}\n")

        # ۲. تست jaam/rooms/{id} برای اولین درس lms3
        print("=== jaam/rooms/{group_id} ===")
        courses = assistant.get_all_courses()
        active = [c for c in courses if c.is_active]

        for course in active[:2]:
            url = f"https://{course.domain}.ui.ac.ir/jaam/rooms/{course.group_id}"
            try:
                r = assistant.client.get(url, timeout=30)
                print(f"\n📚 {course.name} ({course.domain})")
                print(f"  {url}")
                print(f"    → {r.status_code} ({len(r.text)} bytes)")

                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    print(f"    body id: {body.get('id') if body else '?'}")

                    path = Path(f"data/jaam_rooms_{course.group_id}.html")
                    path.write_text(r.text, encoding="utf-8")
                    print(f"    ذخیره: {path}")

                    # دنبال عنوان جلسات
                    for h in soup.find_all(["h1", "h2", "h3", "h4"])[:10]:
                        text = h.get_text(strip=True)
                        if text and len(text) < 100:
                            print(f"    [{h.name}] {text}")

                    # دنبال زمان‌ها
                    for a in soup.find_all("a", href=True):
                        if "/jaam/" in a["href"] and "rooms" not in a["href"]:
                            print(f"    لینک: {a['href'][:80]} → {a.get_text(strip=True)[:50]}")
            except Exception as e:
                print(f"  → خطا: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()