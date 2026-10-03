"""Debug: تست widget endpoint برای اعضا."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant
from src.collectors.members import MembersCollector
from src.parsers.members import MemberParser

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

        collector = MembersCollector(assistant.client, course)
        parser = MemberParser(
            course_id=course.group_id,
            teacher_name=course.teacher,
        )

        # === دانشجویان ===
        print("=" * 60)
        print("دانشجویان (صفحه 1)")
        print("=" * 60)

        html = collector.collect_students(page=1)
        Path("data/widget_students.html").write_text(html, encoding="utf-8")
        print(f"طول HTML: {len(html)}")

        students = parser.parse(html, is_teacher=False)
        print(f"تعداد: {len(students)}\n")
        for s in students:
            print(f"  • {s.name} (id={s.id})")

        # === استادان ===
        print("\n" + "=" * 60)
        print("استادان (صفحه 1)")
        print("=" * 60)

        html2 = collector.collect_admins(page=1)
        Path("data/widget_admins.html").write_text(html2, encoding="utf-8")
        print(f"طول HTML: {len(html2)}")

        teachers = parser.parse(html2, is_teacher=True)
        print(f"تعداد: {len(teachers)}\n")
        for t in teachers:
            print(f"  • {t.name} (id={t.id})")


if __name__ == "__main__":
    main()