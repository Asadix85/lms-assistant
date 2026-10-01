"""تست Sync Service."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.services.lms_assistant import LMSAssistant
from src.services.sync_service import SyncService
from src.storage.database import Database

load_dotenv()


def test_full_sync():
    """تست کامل Sync."""
    # دیتابیس تست
    test_db = Path("data/test_sync.db")
    if test_db.exists():
        test_db.unlink()

    with Database(test_db) as db:
        db.init_schema()

        with LMSAssistant(
            username=os.environ["LMS_USERNAME"],
            password=os.environ["LMS_PASSWORD"],
        ) as assistant:
            assert assistant.login()
            print(f"✅ Login. User ID: {assistant.user_id}\n")

            sync = SyncService(assistant, db)

            # === Sync ۱ (اولین) ===
            print("=" * 60)
            print("🔄 Sync اول (اولین بار)")
            print("=" * 60)

            result1 = sync.sync()
            print(f"\n{result1.summary()}")
            print(f"⏱️  مدت: {result1.duration_seconds:.1f} ثانیه")
            print(f"📊 جدید: {result1.total_new}, به‌روز: {result1.total_updated}")

            assert result1.is_first_sync
            assert not result1.has_error
            print("\n✅ اولین Sync موفق")

            # === Sync ۲ (بدون تغییر) ===
            print("\n" + "=" * 60)
            print("🔄 Sync دوم (بدون تغییر)")
            print("=" * 60)

            result2 = sync.sync()
            print(f"\n{result2.summary()}")
            print(f"⏱️  مدت: {result2.duration_seconds:.1f} ثانیه")

            assert not result2.is_first_sync
            assert result2.total_new == 0, "نباید چیز جدیدی باشد"
            print("\n✅ Sync دوم موفق (هیچ چیز جدید نیست)")

        # آمار نهایی
        from src.storage.repositories import (
            CourseRepository,
            ContentRepository,
            EventRepository,
        )
        print("\n" + "=" * 60)
        print("📊 آمار نهایی دیتابیس")
        print("=" * 60)
        print(f"  دروس: {CourseRepository(db).count()}")
        print(f"  محتوا: {ContentRepository(db).count()}")
        print(f"  رویدادها: {EventRepository(db).count()}")

    # پاکسازی
    if test_db.exists():
        test_db.unlink()
    print("\n🎉 تست موفق!")


if __name__ == "__main__":
    test_full_sync()