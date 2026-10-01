"""تست Course collector و parser."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.collectors.courses import CoursesCollector
from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient
from src.parsers.courses import CourseParser


load_dotenv()


def test_collect_and_parse():
    """تست کامل: لاگین → collect → parse."""
    username = os.environ["LMS_USERNAME"]
    password = os.environ["LMS_PASSWORD"]

    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        # ۱. لاگین
        auth = LMSAuth(client)
        assert auth.login(username, password)

        # ۲. Collect
        collector = CoursesCollector(client)
        html = collector.collect()
        assert len(html) > 1000

        # ذخیره برای دیباگ
        Path("data/nodeclass.html").write_text(html, encoding="utf-8")

        # ۳. Parse
        parser = CourseParser(base_url="https://lms4.ui.ac.ir")
        courses = parser.parse(html)

        # ۴. بررسی
        assert len(courses) > 0, "باید حداقل یک درس پیدا شود"
        print(f"\n✅ {len(courses)} درس پیدا شد:")
        for c in courses:
            print(f"  • {c.name}")
            print(f"    teacher: {c.teacher}")
            print(f"    code: {c.code}")
            print(f"    url: {c.url}")


if __name__ == "__main__":
    test_collect_and_parse()
    print("\n🎉 تست موفق!")