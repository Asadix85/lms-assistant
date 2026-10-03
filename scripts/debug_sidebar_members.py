"""Debug: استخراج همکلاسی‌ها از sidebar صفحه‌ی درس."""

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
        print(f"📚 درس: {course.name} (group_id={course.group_id})\n")

        # GET صفحه wall
        url = f"https://lms4.ui.ac.ir/group/{course.group_id}"
        r = assistant.client.get(url)
        print(f"GET {url} → {r.status_code}\n")

        # ذخیره
        Path(f"data/group_{course.group_id}_full.html").write_text(r.text, encoding="utf-8")

        soup = BeautifulSoup(r.text, "lxml")

        # === پیدا کردن ساختار sidebar ===
        print("=" * 60)
        print("جستجو در layout_right / group_members")
        print("=" * 60)

        # روش ۱: layout_right
        right = soup.find("div", class_="layout_right")
        if right:
            print(f"\n✅ layout_right پیدا شد")
            text = right.get_text(separator=" ", strip=True)[:300]
            print(f"   متن: {text}")

            # لینک‌های profile در sidebar
            profile_links = right.find_all("a", href=lambda h: h and "/profile/" in h)
            print(f"\n   تعداد profile links: {len(profile_links)}")

            for i, a in enumerate(profile_links[:10], 1):
                img = a.find("img")
                img_src = img.get("src", "") if img else ""
                print(f"\n   {i}. {a.get_text(strip=True)}")
                print(f"      href: {a['href']}")
                print(f"      img: {img_src}")

        # === روش ۲: گروه دانشجویان (sh کلاس‌های احتمالی) ===
        print("\n" + "=" * 60)
        print("جستجوی کلاس‌های احتمالی")
        print("=" * 60)

        classes_to_try = [
            "group_members",
            "group-members",
            "members-list",
            "member_list",
            "group_students",
            "students-list",
            "group_profile_members",
        ]

        for cls in classes_to_try:
            el = soup.find(class_=cls)
            if el:
                print(f"\n✅ پیدا شد: .{cls}")
                profiles = el.find_all("a", href=lambda h: h and "/profile/" in h)
                print(f"   تعداد پروفایل: {len(profiles)}")

        # === روش ۳: همه‌ی لینک‌های profile در کل صفحه ===
        print("\n" + "=" * 60)
        print("همه‌ی profile links در کل صفحه")
        print("=" * 60)

        all_profiles = soup.find_all("a", href=lambda h: h and "/profile/" in h)
        print(f"\nتعداد کل: {len(all_profiles)}")

        seen = set()
        for a in all_profiles:
            href = a["href"]
            uid = href.split("/profile/")[-1].split("/")[0]
            if uid in seen:
                continue
            seen.add(uid)

            name = a.get_text(strip=True)
            img = a.find("img")
            img_src = img.get("src", "") if img else ""

            print(f"\n   {name} (id={uid})")
            if img_src:
                print(f"      عکس: {img_src[:80]}")

        print(f"\nجمع یکتا: {len(seen)} کاربر")

        # === روش ۴: چک کردن memberpack ===
        print("\n" + "=" * 60)
        print("تست /groups/index/memberpack/{course_id}")
        print("=" * 60)

        urls = [
            f"https://lms4.ui.ac.ir/groups/index/memberpack/?group_id={course.group_id}",
            f"https://lms4.ui.ac.ir/groups/member/list/group_id/{course.group_id}",
            f"https://lms4.ui.ac.ir/group/member/list/{course.group_id}",
        ]

        for u in urls:
            try:
                r = assistant.client.get(u, timeout=15)
                print(f"\nGET {u}")
                print(f"  → {r.status_code} ({len(r.text)} bytes)")

                if r.status_code == 200 and len(r.text) > 3000:
                    soup2 = BeautifulSoup(r.text, "lxml")
                    body = soup2.find("body")
                    print(f"  body id: {body.get('id') if body else '?'}")

                    profiles = soup2.find_all("a", href=lambda h: h and "/profile/" in h)
                    print(f"  تعداد profile: {len(profiles)}")

                    # ذخیره
                    fname = u.replace("https://", "").replace("/", "_").replace("?", "_").replace("=", "_")
                    Path(f"data/{fname}.html").write_text(r.text, encoding="utf-8")
                    print(f"  ذخیره شد")
            except Exception as e:
                print(f"\nGET {u} → خطا: {e}")


if __name__ == "__main__":
    main()