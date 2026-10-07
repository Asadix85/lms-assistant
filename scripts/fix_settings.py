"""پاکسازی و یکسان‌سازی تنظیمات sync در دیتابیس."""

from src.storage.database import Database
from src.storage.repositories import SettingRepository


OLD_KEYS = ["sync_posts", "sync_assignments"]
NEW_KEYS = [
    "sync_courses",
    "sync_contents",
    "sync_events",
    "sync_wall",
    "sync_members",
]


def main() -> None:
    db = Database("data/lms.db")
    db.init_schema()
    repo = SettingRepository(db)

    print("=" * 50)
    print("🔧 یکسان‌سازی تنظیمات Sync")
    print("=" * 50)

    # === ۱. حذف keyهای قدیمی ===
    for key in OLD_KEYS:
        old_value = repo.get(key, None)
        if old_value is not None:
            print(f"  🗑️  حذف: {key} (بود: {old_value})")
            repo.set(key, "")

    # === ۲. تنظیم keyهای استاندارد ===
    defaults = {
        "sync_courses": "true",
        "sync_contents": "true",
        "sync_events": "true",
        "sync_wall": "true",
        "sync_members": "false",
    }

    for key, default in defaults.items():
        current = repo.get(key, None)
        if current is None or current == "":
            repo.set(key, default)
            print(f"  ➕ تنظیم: {key} = {default}")
        else:
            print(f"  ✅ موجود: {key} = {current}")

    print("=" * 50)
    print("📊 وضعیت نهایی:")
    print("=" * 50)

    for key in NEW_KEYS:
        print(f"  {key:20s} = {repo.get(key, '❌')}")

    print("=" * 50)
    db.close()


if __name__ == "__main__":
    main()