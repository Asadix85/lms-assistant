"""تست Sync با wall (posts + assignments)."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant
from src.services.sync_service import SyncService
from src.storage.database import Database

load_dotenv()


def main():
    db_path = Path("data/test_sync_wall.db")
    if db_path.exists():
        db_path.unlink()

    with Database(db_path) as db:
        db.init_schema()

        with LMSAssistant(
            username=os.environ["LMS_USERNAME"],
            password=os.environ["LMS_PASSWORD"],
        ) as assistant:
            assert assistant.login()

            sync = SyncService(assistant, db)

            # === Sync اول ===
            print("=" * 60)
            print("🔄 Sync اول")
            print("=" * 60)

            result1 = sync.sync()
            print(f"\n{result1.summary()}")
            print(f"⏱️  {result1.duration_seconds:.1f} ثانیه")
            print(f"\n📊 جدید: {result1.total_new}")
            print(f"   - دروس: {result1.courses_new}")
            print(f"   - محتوا: {result1.contents_new}")
            print(f"   - رویدادها: {result1.events_new}")
            print(f"   - پست‌ها: {result1.posts_new}")
            print(f"   - تکالیف: {result1.assignments_new}")

            # === Sync دوم ===
            print("\n" + "=" * 60)
            print("🔄 Sync دوم")
            print("=" * 60)

            result2 = sync.sync()
            print(f"\n{result2.summary()}")
            print(f"⏱️  {result2.duration_seconds:.1f} ثانیه")

            # === آمار نهایی ===
            from src.storage.repositories import (
                AssignmentRepository,
                CourseRepository,
                EventRepository,
                PostRepository,
            )
            print("\n" + "=" * 60)
            print("📊 آمار نهایی")
            print("=" * 60)
            print(f"  دروس: {CourseRepository(db).count()}")
            print(f"  رویدادها: {EventRepository(db).count()}")
            print(f"  پست‌ها: {PostRepository(db).count()}")
            print(f"  تکالیف: {AssignmentRepository(db).count()}")

            # === تکالیف با ددلاین ===
            print("\n📋 تکالیف نزدیک:")
            for a in AssignmentRepository(db).get_upcoming(limit=5):
                print(f"  • {a.title[:60]}")
                print(f"    ددلاین: {a.deadline}")

    if db_path.exists():
        db_path.unlink()
    print("\n🎉 تست موفق!")


if __name__ == "__main__":
    main()