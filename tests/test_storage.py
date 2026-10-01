"""تست storage layer."""

from pathlib import Path

from src.models.course import Course, CourseStatus
from src.models.content import Content
from src.models.event import Event, EventType
from src.storage.database import Database
from src.storage.repositories import (
    CourseRepository,
    ContentRepository,
    EventRepository,
    SettingRepository,
)


def test_database_and_repos():
    """تست کامل: ساخت DB + ذخیره + خواندن."""
    # استفاده از دیتابیس تست
    test_db = Path("data/test_lms.db")
    if test_db.exists():
        test_db.unlink()

    with Database(test_db) as db:
        db.init_schema()
        print("✅ Schema ساخته شد")

        # === Courses ===
        course_repo = CourseRepository(db)

        c1 = Course(
            id="134345",
            name="ساختمان داده",
            url="https://lms4.ui.ac.ir/group/134345",
            group_id="134345",
            domain="lms4",
            teacher="هادی تابع الحجه",
            code="36-20-319",
            status=CourseStatus.ACTIVE,
        )
        course_repo.save(c1)

        c2 = Course(
            id="140060",
            name="دانش خانواده",
            url="https://lms3.ui.ac.ir/nodeg/.../140060/2",
            group_id="140060",
            domain="lms3",
            teacher="محمد عابدینی",
            status=CourseStatus.ACTIVE,
        )
        course_repo.save(c2)

        courses = course_repo.get_all()
        assert len(courses) == 2
        print(f"✅ {len(courses)} درس ذخیره شد")

        # تست UPDATE
        c1.teacher = "استاد جدید"
        course_repo.save(c1)
        updated = course_repo.get_by_id("134345")
        assert updated.teacher == "استاد جدید"
        print("✅ UPDATE کار می‌کند")

        # === Contents ===
        content_repo = ContentRepository(db)

        cont = Content(
            id="hash123",
            course_id="134345",
            title="chapter01.pdf",
            url="https://lms4.ui.ac.ir/public/group/.../178770_62f6.pdf",
            content_type="pdf",
            filename="chapter01.pdf",
        )
        content_repo.save(cont)

        contents = content_repo.get_by_course("134345")
        assert len(contents) == 1
        print(f"✅ {len(contents)} محتوا ذخیره شد")

        # === Events ===
        event_repo = EventRepository(db)

        e1 = Event(
            id="event1",
            course_id="134345",
            title="ساختمان داده-جلسه 3",
            event_type=EventType.LIVE_SESSION,
            url="https://lms4.ui.ac.ir/jaam/joinfast/.../134",
            room_token="ABC123",
        )
        event_repo.save(e1)

        events = event_repo.get_all()
        assert len(events) == 1
        print(f"✅ {len(events)} رویداد ذخیره شد")

        # === Settings ===
        setting_repo = SettingRepository(db)
        setting_repo.set("last_sync", "2026-10-01T12:00:00")
        assert setting_repo.get("last_sync") == "2026-10-01T12:00:00"
        print("✅ Settings کار می‌کند")

        # === آمار ===
        print(f"\n📊 آمار:")
        print(f"   Courses: {course_repo.count()}")
        print(f"   Contents: {content_repo.count()}")
        print(f"   Events: {event_repo.count()}")

    # پاکسازی
    if test_db.exists():
        test_db.unlink()
    print("\n🎉 تست موفق!")


if __name__ == "__main__":
    test_database_and_repos()