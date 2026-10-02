"""تست ذخیره Post و Assignment در دیتابیس."""

from pathlib import Path

from src.models.course import Course, CourseStatus
from src.parsers.wall import WallParser
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    PostRepository,
)


def main():
    # دیتابیس جدید
    db_path = Path("data/test_wall.db")
    if db_path.exists():
        db_path.unlink()

    with Database(db_path) as db:
        db.init_schema()
        print("✅ Schema ساخته شد")

        # ⚠️ اول درس رو ذخیره کن (چون FK داریم)
        course = Course(
            id="139710",
            name="مدارهای الکتریکی و الکترونیکی",
            url="https://lms4.ui.ac.ir/group/139710",
            group_id="139710",
            domain="lms4",
            teacher="کمال جمشیدی",
            status=CourseStatus.ACTIVE,
        )
        CourseRepository(db).save(course)
        print(f"✅ درس ذخیره شد: {course.name}")

        # حالا Post و Assignment
        html = Path("data/wall_139710.html").read_text(encoding="utf-8")
        parser = WallParser(course_id="139710")
        posts, assignments = parser.parse(html)

        # ذخیره
        post_repo = PostRepository(db)
        for p in posts:
            post_repo.save(p)

        assign_repo = AssignmentRepository(db)
        for a in assignments:
            assign_repo.save(a)

        print(f"\n📝 {post_repo.count()} پست ذخیره شد")
        print(f"📋 {assign_repo.count()} تکلیف ذخیره شد")

        # خواندن
        print(f"\n📝 Postها از DB:")
        for p in post_repo.get_by_course("139710"):
            print(f"  • {p.author}: {p.text[:50]}")
            print(f"    {p.posted_at}")

        print(f"\n📋 تکالیف از DB:")
        for a in assign_repo.get_upcoming():
            print(f"  • {a.title[:60]}")
            print(f"    ددلاین: {a.deadline}")

    # پاکسازی
    if db_path.exists():
        db_path.unlink()
    print("\n🎉 تست موفق!")


if __name__ == "__main__":
    main()