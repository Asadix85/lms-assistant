"""تست Quera Sync."""

from config.settings import settings
from src.storage.database import Database
from src.services.quera_sync import QueraSyncService


def main() -> None:
    if not settings.quera_username or not settings.quera_password:
        print("❌ QUERA_USERNAME و QUERA_PASSWORD رو توی .env تنظیم کن")
        return

    print("=" * 50)
    print("🧪 تست Quera Sync")
    print("=" * 50)

    with Database("data/lms.db") as db:
        db.init_schema()

        sync = QueraSyncService(
            username=settings.quera_username,
            password=settings.quera_password,
            db=db,
        )

        result = sync.sync()

        print("\n" + "=" * 50)
        print("📊 نتیجه:")
        print("=" * 50)
        print(f"  🆕 جدید: {result['new']}")
        print(f"  🔄 به‌روزرسانی: {result['updated']}")
        print(f"  📋 کل: {result['total']}")
        print(f"  ⏱️ زمان: {result['duration']:.2f}s")

        if result["error"]:
            print(f"  ❌ خطا: {result['error']}")

        # نمایش لیست
        print("\n" + "=" * 50)
        print("📋 تمرین‌ها:")
        print("=" * 50)

        from src.storage.repositories import QueraAssignmentRepository
        repo = QueraAssignmentRepository(db)
        for a in repo.get_all():
            print(f"\n  🎯 {a.name}")
            print(f"     📚 {a.course_name}")
            print(f"     ⏰ {a.finish_time}")
            print(f"     📊 {a.submitted_count}/{a.problems_count}")


if __name__ == "__main__":
    main()