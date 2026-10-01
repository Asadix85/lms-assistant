"""تست: دریافت محتوای lms3 از چند درس."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.services.lms_assistant import LMSAssistant
from src.parsers.contents import ContentParser

load_dotenv()


def test_course(assistant, course):
    """تست محتوای یک درس."""
    print(f"\n{'='*60}")
    print(f"📚 {course.name} (group_id={course.group_id})")
    print('='*60)

    # GET listofcontent از دامنه‌ی مربوطه
    if course.domain == "lms4":
        url = f"https://lms4.ui.ac.ir/group/index/listofcontent/?group_id={course.group_id}"
        base_url = "https://lms4.ui.ac.ir"
    else:
        url = f"https://lms3.ui.ac.ir/group/index/listofcontent/?group_id={course.group_id}"
        base_url = "https://lms3.ui.ac.ir"

    r = assistant.client.get(url)
    print(f"GET {url}")
    print(f"→ {r.status_code} ({len(r.text)} bytes)\n")

    # ذخیره
    Path("data").mkdir(exist_ok=True)
    path = Path(f"data/{course.domain}_listofcontent_{course.group_id}.html")
    path.write_text(r.text, encoding="utf-8")
    print(f"ذخیره: {path}\n")

    # Parse
    parser = ContentParser(course_id=course.group_id, base_url=base_url)
    contents = parser.parse(r.text)
    print(f"📄 {len(contents)} فایل:")
    for c in contents:
        print(f"  • {c.title} ({c.content_type})")
        print(f"    {c.url}")

    # اگر ۰ بود، HTML رو بررسی کن
    if not contents:
        print("\n🔍 بررسی HTML (خام):")
        soup = BeautifulSoup(r.text, "lxml")

        # همه لینک‌های /public/ یا با پسوند
        print("  همه لینک‌های /public/ یا با پسوند:")
        found = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/public/" in href or any(
                href.lower().endswith(ext)
                for ext in [".pdf", ".zip", ".docx", ".pptx", ".mp4"]
            ):
                print(f"    {href}")
                found += 1
        if found == 0:
            print("    (هیچ لینکی پیدا نشد)")

        # پسوندها در کل HTML
        print("\n  پسوندها در HTML خام:")
        for ext in [".pdf", ".zip", ".docx", ".pptx", ".doc", ".mp4", "/public/"]:
            count = r.text.lower().count(ext)
            print(f"    {ext}: {count}")


def main():
    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()
        courses = assistant.get_all_courses()

        # انتخاب ۴ درس مختلف: ۲ lms3، ۲ lms4
        lms3 = [c for c in courses if c.domain == "lms3" and c.is_active]
        lms4 = [c for c in courses if c.domain == "lms4" and c.is_active]

        print(f"\n🟢 lms3: {len(lms3)} درس")
        print(f"🔵 lms4: {len(lms4)} درس")

        # تست ۲ درس lms3
        for c in lms3[:2]:
            test_course(assistant, c)

        # تست ۲ درس lms4
        for c in lms4[:2]:
            test_course(assistant, c)


if __name__ == "__main__":
    main()