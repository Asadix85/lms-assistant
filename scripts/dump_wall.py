"""ذخیره‌ی HTML wall یه درس برای debug."""

from pathlib import Path

from config.settings import settings
from src.collectors.wall import WallCollector
from src.services.lms_assistant import LMSAssistant


def main() -> None:
    with LMSAssistant(settings.lms_username, settings.lms_password) as a:
        if not a.login():
            print("❌ Login ناموفق")
            return

        courses = a.get_all_courses()
        active = [c for c in courses if c.is_active]

        if not active:
            print("❌ درس فعالی نیست")
            return

        # اولین درس فعال
        course = active[0]
        print(f"📚 درس: {course.name}")
        print(f"🔢 کد: {course.group_id}")
        print(f"🌐 دامنه: {course.domain}")

        # فعال‌سازی دامنه
        if course.domain not in a.active_domains and course.nodeg_url:
            print(f"🔓 فعال‌سازی دامنه {course.domain}...")
            a.activate_domain(course.nodeg_url, course.domain)

        # گرفتن HTML
        print("📥 دریافت HTML wall...")
        collector = WallCollector(a.client, course=course)
        html = collector.collect()

        if not html:
            print("❌ HTML خالی")
            return

        # ذخیره
        out = Path("debug_wall.html")
        out.write_text(html, encoding="utf-8")
        print(f"✅ ذخیره شد: {out} ({len(html)} کاراکتر)")


if __name__ == "__main__":
    main()