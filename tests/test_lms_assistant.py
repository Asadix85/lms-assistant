"""تست LMSAssistant."""

import os
from collections import Counter

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def test_full_flow():
    """تست کامل: login + همه درس‌ها + فعال‌سازی دامنه‌ها."""
    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        # ۱. Login
        assert assistant.login(), "Login باید موفق باشد"
        print(f"✅ Login موفق. User ID: {assistant.user_id}")

        # ۲. همه درس‌ها
        courses = assistant.get_all_courses()
        print(f"\n📚 {len(courses)} درس پیدا شد:\n")

        # گروه‌بندی بر اساس دامنه
        by_domain = Counter(c.domain for c in courses)
        icons = {"lms3": "🟢", "lms4": "🔵", "lms5": "🔴"}

        for domain in sorted(by_domain):
            icon = icons.get(domain, "⚪")
            print(f"{icon} {domain}: {by_domain[domain]} درس")

        print("\nجزئیات:")
        for c in courses:
            icon = icons.get(c.domain, "⚪")
            status = "✓" if c.is_active else "✗"
            print(f"  {icon} [{status}] {c.name}")
            print(f"      teacher: {c.teacher}")
            print(f"      code: {c.code}")
            print(f"      domain: {c.domain}")

        # ۳. دامنه‌های فعال
        print(f"\n🌐 دامنه‌های فعال: {sorted(assistant.active_domains)}")

        # بررسی
        assert len(courses) >= 10, "باید حداقل ۱۰ درس باشد"


if __name__ == "__main__":
    test_full_flow()
    print("\n🎉 تست موفق!")