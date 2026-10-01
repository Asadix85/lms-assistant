"""تست: دریافت محتوای همه دروس فعال."""

import os

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def test_all_contents():
    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()
        print(f"✅ Login. User ID: {assistant.user_id}\n")

        # همه محتوا
        all_contents = assistant.get_all_contents()

        print(f"\n{'='*60}")
        print(f"📊 خلاصه محتوا")
        print('='*60)

        total_files = 0
        for course_id, contents in all_contents.items():
            print(f"\n📚 درس {course_id}: {len(contents)} فایل")
            for c in contents:
                print(f"  • {c.title} ({c.content_type})")
            total_files += len(contents)

        print(f"\n🎯 جمع کل: {total_files} فایل در {len(all_contents)} درس")


if __name__ == "__main__":
    test_all_contents()
    print("\n🎉 تست موفق!")