"""حذف و ساخت مجدد جدول course_schedules."""

from src.storage.database import Database


def main() -> None:
    db = Database("data/lms.db")
    db.init_schema()

    print("🗑️  حذف جدول قدیمی...")
    db.connection.execute("DROP TABLE IF EXISTS course_schedules")
    db.connection.commit()
    print("✅ جدول قدیمی حذف شد")

    print("🔨 ساخت جدول جدید...")
    db.init_schema()
    db.connection.commit()
    print("✅ جدول جدید ساخته شد")

    print("\n📋 ستون‌های جدول:")
    cols = db.fetch_all("PRAGMA table_info(course_schedules)")
    for c in cols:
        print(f"  • {c['name']}: {c['type']}")

    db.close()


if __name__ == "__main__":
    main()