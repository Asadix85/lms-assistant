"""سیستم مهاجرت (Migration) دیتابیس.

نسخه‌ی Schema در جدول `schema_version` نگه داشته می‌شود و مهاجرت‌ها
به‌صورت ترتیبی و داخل تراکنش اعمال می‌شوند. برای افزودن تغییر جدید:

1. یک تابع `_migrate_to_N` بسازید (N = نسخه‌ی بعدی).
2. آن را به لیست `MIGRATIONS` در انتهای فایل اضافه کنید.
"""

import sqlite3

from loguru import logger

# نسخه‌ی اولیه — همان schema.sql موجود
INITIAL_VERSION = 1


def get_version(conn: sqlite3.Connection) -> int:
    """نسخه‌ی فعلی Schema را برمی‌گرداند (۰ اگر جدول نسخه وجود نداشته باشد)."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if not row:
        return 0
    result = conn.execute(
        "SELECT MAX(version) FROM schema_version"
    ).fetchone()
    return result[0] or 0


def set_version(conn: sqlite3.Connection, version: int) -> None:
    """ثبت نسخه‌ی جدید."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "  version INTEGER PRIMARY KEY,"
        "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )
    conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (version,))


# === مهاجرت‌ها ===
# هر مهاجرت: (target_version, callable)


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """نام ستون‌های یک جدول."""
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _migrate_to_2(conn: sqlite3.Connection) -> None:
    """افزودن پشتیبانی تکلیف دستی + وضعیت انجام‌شده (is_manual / is_done)."""
    for table in ("assignments", "quera_assignments"):
        cols = _table_columns(conn, table)
        if "is_manual" not in cols:
            conn.execute(
                f"ALTER TABLE {table} "
                "ADD COLUMN is_manual INTEGER NOT NULL DEFAULT 0"
            )
        if "is_done" not in cols:
            conn.execute(
                f"ALTER TABLE {table} "
                "ADD COLUMN is_done INTEGER NOT NULL DEFAULT 0"
            )


MIGRATIONS: list[tuple[int, object]] = [
    (2, _migrate_to_2),
]


def migrate(conn: sqlite3.Connection) -> None:
    """اعمال تمام مهاجرت‌های انجام‌نشده، به‌ترتیب و داخل تراکنش."""
    current = get_version(conn)

    # دیتابیسی که از قبل جداولش ساخته شده اما جدول نسخه ندارد → نسخه‌ی اولیه
    if current == 0:
        tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name!='schema_version'"
        ).fetchone()[0]
        if tables > 0:
            logger.info(f"دیتابیس قدیمی شناسایی شد — نسخه‌ی اولیه {INITIAL_VERSION} ست می‌شود")
            set_version(conn, INITIAL_VERSION)
            conn.commit()
            current = INITIAL_VERSION
        else:
            current = 0

    pending = [(v, fn) for v, fn in MIGRATIONS if v > current]
    if not pending:
        return

    for target_version, migration_fn in sorted(pending):
        logger.info(f"⬆️ اجرای مهاجرت به نسخه {target_version}")
        try:
            conn.execute("BEGIN")
            migration_fn(conn)  # type: ignore[operator]
            set_version(conn, target_version)
            conn.commit()
            logger.info(f"✅ مهاجرت نسخه {target_version} انجام شد")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"❌ خطا در مهاجرت نسخه {target_version}: {e} — rollback شد")
            raise
