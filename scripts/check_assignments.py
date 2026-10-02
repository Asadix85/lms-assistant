"""بررسی تکالیف در LMS و دیتابیس."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant
from src.storage.database import Database
from src.storage.repositories import AssignmentRepository

load_dotenv()


def main():
    print("=" * 60)
    print("تکالیف در دیتابیس:")
    print("=" * 60)

    with Database("data/lms.db") as db:
        db_repo = AssignmentRepository(db)
        db_assignments = db_repo.get_all()
        for a in db_assignments:
            print(f"  ID: {a.id}")
            print(f"  Title: {a.title[:60]}...")
            print(f"  Course: {a.course_id}")
            print(f"  Deadline: {a.deadline}")
            print()

    print("\n" + "=" * 60)
    print("تکالیف در LMS (در همه دروس):")
    print("=" * 60)

    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()

        courses = assistant.get_active_courses()
        print(f"\nتعداد دروس فعال: {len(courses)}\n")

        total_assignments = 0
        for course in courses:
            posts, assignments = assistant.get_course_wall(course)
            if assignments:
                print(f"📚 {course.name} ({course.domain}):")
                for a in assignments:
                    print(f"  ID: {a.id}")
                    print(f"  Title: {a.title[:80]}...")
                    print(f"  Deadline: {a.deadline}")
                    print(f"  Length: {len(a.title)}")
                    print()
                    total_assignments += 1

        print(f"\nجمع کل: {total_assignments} تکلیف در LMS")


if __name__ == "__main__":
    main()