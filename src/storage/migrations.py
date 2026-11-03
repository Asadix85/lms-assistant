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


def _migrate_to_3(conn: sqlite3.Connection) -> None:
    """جداول هویت وب: users / web_sessions / user_secrets."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            lms_username TEXT NOT NULL UNIQUE,
            lms_user_id TEXT,
            full_name TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            last_login_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_users_lms_username ON users(lms_username);

        CREATE TABLE IF NOT EXISTS web_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_web_sessions_user ON web_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_web_sessions_token ON web_sessions(token_hash);
        CREATE INDEX IF NOT EXISTS idx_web_sessions_expires ON web_sessions(expires_at);

        CREATE TABLE IF NOT EXISTS user_secrets (
            user_id TEXT PRIMARY KEY,
            lms_password_enc TEXT,
            quera_username TEXT,
            quera_password_enc TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )


MIGRATIONS: list[tuple[int, object]] = [
    (2, _migrate_to_2),
    (3, _migrate_to_3),
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
            # اگر تراکنش بازِ خودکار (autocommit معکول) وجود داشته باشد،
            # ابتدا commit می‌شود تا «BEGIN داخل BEGIN» رخ ندهد.
            if conn.in_transaction:
                conn.commit()
            conn.execute("BEGIN")
            migration_fn(conn)  # type: ignore[operator]
            set_version(conn, target_version)
            conn.commit()
            logger.info(f"✅ مهاجرت نسخه {target_version} انجام شد")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"❌ خطا در مهاجرت نسخه {target_version}: {e} — rollback شد")
            raise
