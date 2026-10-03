"""Debug: تحلیل عمیق لینک‌های profile در wall."""

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

        courses = assistant.get_all_courses()
        course = next(c for c in courses if c.domain == "lms4" and c.is_active)
        print(f"📚 درس: {course.name}")
        print(f"   استاد: {course.teacher}\n")

        # GET صفحه wall
        url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
        r = assistant.client.get(url)
        soup = BeautifulSoup(r.text, "lxml")

        # === پیدا کردن همه profile links با کانتکست ===
        print("=" * 60)
        print("Profile links با کانتکست:")
        print("=" * 60)

        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/profile/" not in href:
                continue

            # user_id
            user_id = href.split("/profile/")[-1].split("/")[0]
            if user_id in seen:
                continue
            seen.add(user_id)

            name = a.get_text(strip=True)

            # parent برای کانتکست
            parent = a.find_parent(["li", "div"])
            parent_text = ""
            if parent:
                parent_text = parent.get_text(separator=" ", strip=True)[:150]

            # آیا در wall feed هست؟
            in_feed = bool(a.find_parent(class_="feed_item"))

            print(f"\n👤 {name}")
            print(f"   user_id: {user_id}")
            print(f"   href: {href}")
            print(f"   در wall: {in_feed}")
            print(f"   کانتکست: {parent_text}")

            # آیا عکس داره؟
            img = a.find("img") or parent.find("img") if parent else None
            if img and img.get("src"):
                print(f"   عکس: {img['src'][:80]}")

        # === فیلتر استاد از همکلاسی ===
        print("\n" + "=" * 60)
        print("فیلتر استاد vs همکلاسی:")
        print("=" * 60)

        teacher_name = (course.teacher or "").strip()
        # استاد ممکنه با "استاد" شروع بشه
        teacher_name_clean = teacher_name.replace("استاد ", "").strip()

        students = []
        teachers = []

        for user_id in seen:
            # پیدا کردن اسمش
            for a in soup.find_all("a", href=f"/profile/{user_id}"):
                name = a.get_text(strip=True)
                if not name:
                    continue

                # مقایسه با نام استاد
                if teacher_name_clean and teacher_name_clean in name:
                    teachers.append((user_id, name))
                else:
                    students.append((user_id, name))
                break

        print(f"\n👨‍🏫 اساتید ({len(teachers)}):")
        for uid, name in teachers:
            print(f"   {name} (id={uid})")

        print(f"\n👥 همکلاسی‌ها ({len(students)}):")
        for uid, name in students:
            print(f"   {name} (id={uid})")


if __name__ == "__main__":
    main()