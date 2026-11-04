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


def _migrate_to_4(conn: sqlite3.Connection) -> None:
    """چندکاربره کردن جداول دیتا: ستون user_id + PK مرکب."""
    conn.execute("PRAGMA foreign_keys = OFF")

    def has_col(table: str, col: str) -> bool:
        return col in _table_columns(conn, table)

    def table_exists(name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row is not None

    # --- courses ---
    if table_exists("courses") and not has_col("courses", "user_id"):
        conn.executescript(
            """
            CREATE TABLE courses_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                group_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                nodeg_url TEXT,
                teacher TEXT,
                teacher_photo_url TEXT,
                code TEXT,
                term TEXT,
                status TEXT NOT NULL DEFAULT 'unknown',
                is_new INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO courses_v4 (
                user_id, id, name, url, group_id, domain, nodeg_url,
                teacher, teacher_photo_url, code, term, status,
                is_new, first_seen_at, last_seen_at
            )
            SELECT '', id, name, url, group_id, domain, nodeg_url,
                   teacher, teacher_photo_url, code, term, status,
                   is_new, first_seen_at, last_seen_at
            FROM courses;
            DROP TABLE courses;
            ALTER TABLE courses_v4 RENAME TO courses;
            CREATE INDEX IF NOT EXISTS idx_courses_user ON courses(user_id);
            CREATE INDEX IF NOT EXISTS idx_courses_domain ON courses(domain);
            CREATE INDEX IF NOT EXISTS idx_courses_group_id ON courses(group_id);
            """
        )

    # --- members ---
    if table_exists("members") and not has_col("members", "user_id"):
        conn.executescript(
            """
            CREATE TABLE members_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                name TEXT NOT NULL,
                profile_url TEXT NOT NULL,
                member_type TEXT NOT NULL DEFAULT 'unknown',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id, course_id)
            );
            INSERT INTO members_v4 (
                user_id, id, course_id, name, profile_url, member_type,
                first_seen_at, last_seen_at
            )
            SELECT '', id, course_id, name, profile_url, member_type,
                   first_seen_at, last_seen_at
            FROM members;
            DROP TABLE members;
            ALTER TABLE members_v4 RENAME TO members;
            CREATE INDEX IF NOT EXISTS idx_members_user ON members(user_id);
            CREATE INDEX IF NOT EXISTS idx_members_course ON members(course_id);
            """
        )

    # --- contents ---
    if table_exists("contents") and not has_col("contents", "user_id"):
        conn.executescript(
            """
            CREATE TABLE contents_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                is_new INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO contents_v4
            SELECT '', id, course_id, title, url, content_type, filename,
                   is_new, first_seen_at, last_seen_at FROM contents;
            DROP TABLE contents;
            ALTER TABLE contents_v4 RENAME TO contents;
            CREATE INDEX IF NOT EXISTS idx_contents_user ON contents(user_id);
            CREATE INDEX IF NOT EXISTS idx_contents_course ON contents(course_id);
            """
        )

    # --- events ---
    if table_exists("events") and not has_col("events", "user_id"):
        conn.executescript(
            """
            CREATE TABLE events_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                course_id TEXT,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                url TEXT,
                room_token TEXT,
                start_at TEXT,
                end_at TEXT,
                description TEXT,
                is_new INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO events_v4
            SELECT '', id, course_id, title, event_type, url, room_token,
                   start_at, end_at, description, is_new, first_seen_at, last_seen_at
            FROM events;
            DROP TABLE events;
            ALTER TABLE events_v4 RENAME TO events;
            CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
            CREATE INDEX IF NOT EXISTS idx_events_course ON events(course_id);
            CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);
            """
        )

    # --- posts ---
    if table_exists("posts") and not has_col("posts", "user_id"):
        conn.executescript(
            """
            CREATE TABLE posts_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                author TEXT NOT NULL,
                author_id TEXT,
                text TEXT NOT NULL,
                posted_at TEXT,
                posted_at_jalali TEXT,
                post_url TEXT,
                is_new INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO posts_v4
            SELECT '', id, course_id, author, author_id, text, posted_at,
                   posted_at_jalali, post_url, is_new, first_seen_at, last_seen_at
            FROM posts;
            DROP TABLE posts;
            ALTER TABLE posts_v4 RENAME TO posts;
            CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
            CREATE INDEX IF NOT EXISTS idx_posts_course ON posts(course_id);
            """
        )

    # --- assignments ---
    if table_exists("assignments") and not has_col("assignments", "user_id"):
        conn.executescript(
            """
            CREATE TABLE assignments_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                post_id TEXT,
                start_at TEXT,
                deadline TEXT,
                start_at_jalali TEXT,
                deadline_jalali TEXT,
                submit_url TEXT,
                view_url TEXT,
                response_count INTEGER NOT NULL DEFAULT 0,
                is_new INTEGER NOT NULL DEFAULT 0,
                is_manual INTEGER NOT NULL DEFAULT 0,
                is_done INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO assignments_v4
            SELECT '', id, course_id, title, description, post_id,
                   start_at, deadline, start_at_jalali, deadline_jalali,
                   submit_url, view_url, response_count, is_new,
                   COALESCE(is_manual, 0), COALESCE(is_done, 0),
                   first_seen_at, last_seen_at
            FROM assignments;
            DROP TABLE assignments;
            ALTER TABLE assignments_v4 RENAME TO assignments;
            CREATE INDEX IF NOT EXISTS idx_assignments_user ON assignments(user_id);
            CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
            CREATE INDEX IF NOT EXISTS idx_assignments_deadline ON assignments(deadline);
            """
        )

    # --- changes ---
    if table_exists("changes") and not has_col("changes", "user_id"):
        conn.executescript(
            """
            CREATE TABLE changes_v4 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                course_id TEXT,
                data TEXT,
                detected_at TEXT NOT NULL
            );
            INSERT INTO changes_v4 (user_id, type, entity_type, entity_id, course_id, data, detected_at)
            SELECT '', type, entity_type, entity_id, course_id, data, detected_at FROM changes;
            DROP TABLE changes;
            ALTER TABLE changes_v4 RENAME TO changes;
            CREATE INDEX IF NOT EXISTS idx_changes_user ON changes(user_id);
            CREATE INDEX IF NOT EXISTS idx_changes_detected ON changes(detected_at);
            """
        )

    # --- settings ---
    if table_exists("settings") and not has_col("settings", "user_id"):
        conn.executescript(
            """
            CREATE TABLE settings_v4 (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            );
            INSERT INTO settings_v4 (user_id, key, value, updated_at)
            SELECT '', key, value, updated_at FROM settings;
            DROP TABLE settings;
            ALTER TABLE settings_v4 RENAME TO settings;
            """
        )

    # --- course_schedules ---
    if table_exists("course_schedules") and not has_col("course_schedules", "user_id"):
        conn.executescript(
            """
            CREATE TABLE course_schedules_v4 (
                user_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                course_code TEXT,
                sessions_json TEXT,
                raw_text TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, course_id)
            );
            INSERT INTO course_schedules_v4
            SELECT '', course_id, course_code, sessions_json, raw_text,
                   first_seen_at, last_seen_at FROM course_schedules;
            DROP TABLE course_schedules;
            ALTER TABLE course_schedules_v4 RENAME TO course_schedules;
            CREATE INDEX IF NOT EXISTS idx_course_schedules_user ON course_schedules(user_id);
            """
        )

    # --- quera_assignments ---
    if table_exists("quera_assignments") and not has_col("quera_assignments", "user_id"):
        conn.executescript(
            """
            CREATE TABLE quera_assignments_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                name TEXT NOT NULL,
                course_name TEXT,
                finish_time TEXT,
                problems_json TEXT,
                problems_count INTEGER NOT NULL DEFAULT 0,
                submitted_count INTEGER NOT NULL DEFAULT 0,
                is_new INTEGER NOT NULL DEFAULT 0,
                is_manual INTEGER NOT NULL DEFAULT 0,
                is_done INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO quera_assignments_v4
            SELECT '', id, name, course_name, finish_time, problems_json,
                   problems_count, submitted_count, is_new,
                   COALESCE(is_manual, 0), COALESCE(is_done, 0),
                   first_seen_at, last_seen_at
            FROM quera_assignments;
            DROP TABLE quera_assignments;
            ALTER TABLE quera_assignments_v4 RENAME TO quera_assignments;
            CREATE INDEX IF NOT EXISTS idx_quera_assignments_user ON quera_assignments(user_id);
            """
        )

    # --- quera_courses ---
    if table_exists("quera_courses") and not has_col("quera_courses", "user_id"):
        conn.executescript(
            """
            CREATE TABLE quera_courses_v4 (
                user_id TEXT NOT NULL,
                id TEXT NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                teacher TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                assignments_count INTEGER NOT NULL DEFAULT 0,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                PRIMARY KEY (user_id, id)
            );
            INSERT INTO quera_courses_v4
            SELECT '', id, name, url, teacher, is_active, assignments_count,
                   first_seen_at, last_seen_at FROM quera_courses;
            DROP TABLE quera_courses;
            ALTER TABLE quera_courses_v4 RENAME TO quera_courses;
            CREATE INDEX IF NOT EXISTS idx_quera_courses_user ON quera_courses(user_id);
            """
        )

    conn.execute("PRAGMA foreign_keys = ON")


MIGRATIONS: list[tuple[int, object]] = [
    (2, _migrate_to_2),
    (3, _migrate_to_3),
    (4, _migrate_to_4),
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
