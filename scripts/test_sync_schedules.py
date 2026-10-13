"""تست sync برنامه‌ی هفتگی."""

from config.settings import settings
from src.services.lms_assistant import LMSAssistant
from src.services.sync_service import SyncService
from src.storage.database import Database
from src.storage.repositories.course_schedule_repo import CourseScheduleRepository


def main() -> None:
    with Database("data/lms.db") as db:
        db.init_schema()

        with LMSAssistant(settings.lms_username, settings.lms_password) as assistant:
            if not assistant.login():
                print("❌ Login ناموفق")
                return

            print("✅ Login موفق")

            # Sync فقط schedules
            print("\n📅 تست Sync برنامه‌ی هفتگی...")
            sync = SyncService(assistant, db)

            courses = assistant.get_all_courses()
            active = [c for c in courses if c.is_active]

            print(f"📚 {len(active)} درس فعال")

            sync._sync_schedules(None, active)

            # نمایش نتایج
            print("\n" + "=" * 60)
            print("📋 برنامه‌های ذخیره‌شده:")
            print("=" * 60)

            repo = CourseScheduleRepository(db)
            schedules = repo.get_all()

            for s in schedules:
                print(f"\n🎯 درس: {s.course_id}")
                print(f"   📋 کد: {s.course_code}")
                for session in s.sessions:
                    print(f"   • {session.weekday} | {session.time_range}")
                    print(f"     📍 {session.location}")


if __name__ == "__main__":
    main()