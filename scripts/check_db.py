"""بررسی جداول دیتابیس."""

from src.storage.database import Database


def main() -> None:
    db = Database("data/lms.db")
    db.init_schema()

    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )

    print("=" * 50)
    print(f"📋 {len(tables)} جدول توی دیتابیس:")
    print("=" * 50)

    for t in tables:
        # تعداد رکوردها
        try:
            count = db.fetch_one(f"SELECT COUNT(*) as n FROM {t['name']}")["n"]
        except Exception:
            count = "?"

        print(f"  • {t['name']:30s} → {count} رکورد")

    db.close()


if __name__ == "__main__":
    main()