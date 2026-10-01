"""تست محتوای درس."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.collectors.contents import ContentsCollector
from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient
from src.parsers.contents import ContentParser


load_dotenv()


def test_contents_for_course():
    """تست کامل: لاگین → collect → parse برای یک درس."""
    # درس ساختمان داده
    COURSE_ID = "134345"

    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        # ۱. لاگین
        auth = LMSAuth(client)
        assert auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"])

        # ۲. Collect
        collector = ContentsCollector(client, course_id=COURSE_ID)
        html = collector.collect()
        assert len(html) > 1000

        # ۳. Parse
        parser = ContentParser(course_id=COURSE_ID)
        contents = parser.parse(html)

        # ۴. بررسی
        assert len(contents) > 0, "باید حداقل یک فایل پیدا شود"
        print(f"\n✅ {len(contents)} فایل در درس {COURSE_ID}:")
        for c in contents:
            print(f"  • {c.title}")
            print(f"    type: {c.content_type}")
            print(f"    url: {c.url}")
            print(f"    id: {c.id}")


if __name__ == "__main__":
    test_contents_for_course()
    print("\n🎉 تست موفق!")