"""بررسی تنظیمات sync در دیتابیس."""

from src.storage.database import Database
from src.storage.repositories import SettingRepository


KEYS = [
    "sync_members",
    "sync_contents",
    "sync_events",
    "sync_wall",
    "sync_courses",
    "sync_posts",
    "sync_assignments",
    "first_sync",
    "last_sync",
]


def main() -> None:
    db = Database("data/lms.db")
    db.init_schema()
    repo = SettingRepository(db)

    print("=" * 50)
    print("📊 تنظیمات Sync در دیتابیس")
    print("=" * 50)

    for key in KEYS:
        value = repo.get(key, "❌ NOT SET")
        print(f"  {key:20s} = {value}")

    print("=" * 50)
    db.close()


if __name__ == "__main__":
    main()