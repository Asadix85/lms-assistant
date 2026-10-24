"""Database wrapper برای SQLite."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from loguru import logger

from src.core.exceptions import StorageError
from src.storage.migrations import get_version


class Database:
    """مدیریت اتصال و عملیات SQLite.

    اتصال‌ها به‌صورت thread-local نگهداری می‌شوند تا سرویس‌های پس‌زمینه
    (مثل sync در thread جدا) و handlerهای وب بتوانند همزمان از دیتابیس
    استفاده کنند (WAL اجازه‌ی reader همزمان با writer را می‌دهد).
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._all_connections: list[sqlite3.Connection] = []

    # === Connection ===

    def connect(self) -> sqlite3.Connection:
        """اتصال به دیتابیس (اگر نبود، می‌سازد) — یک اتصال مستقل برای هر thread."""
        conn: sqlite3.Connection | None = getattr(self._local, "connection", None)
        if conn is None:
            # اطمینان از وجود پوشه
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            self._local.connection = conn
            self._all_connections.append(conn)
            logger.debug(
                f"اتصال به دیتابیس (thread={threading.get_ident()}): {self.db_path}"
            )

        return conn

    @property
    def connection(self) -> sqlite3.Connection:
        """دسترسی به اتصال thread فعلی."""
        return self.connect()

    # === Init ===

    def init_schema(self, schema_path: str | Path | None = None) -> None:
        """ساخت جداول از فایل schema.sql."""
        if schema_path is None:
            # ⚠️ توی EXE، schema.sql توی _internal هست
            from src.utils.paths import is_frozen

            if is_frozen():
                # توی EXE: از _MEIPASS
                import sys
                schema_path = Path(sys._MEIPASS) / "src" / "storage" / "schema.sql"
            else:
                # توی Python: از مسیر فعلی
                schema_path = Path(__file__).parent / "schema.sql"

        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise StorageError(f"فایل schema پیدا نشد: {schema_path}")

        schema = schema_path.read_text(encoding="utf-8")

        try:
            self.connection.executescript(schema)
            # ثبت نسخه‌ی اولیه و اعمال مهاجرت‌های انجام‌نشده
            from src.storage.migrations import INITIAL_VERSION, migrate, set_version

            if get_version(self.connection) == 0:
                set_version(self.connection, INITIAL_VERSION)
            migrate(self.connection)
            self.connection.commit()
            logger.info(f"✅ Schema ساخته شد: {schema_path.name}")
        except sqlite3.Error as e:
            raise StorageError(f"خطا در ساخت schema: {e}") from e

    # === Query Helpers ===

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager برای تراکنش."""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(
        self,
        sql: str,
        params: tuple | dict | None = None,
    ) -> sqlite3.Cursor:
        """اجرای یک کوئری."""
        try:
            cursor = self.connection.execute(sql, params or ())
            return cursor
        except sqlite3.Error as e:
            raise StorageError(f"خطا در اجرای SQL: {e}\nSQL: {sql}") from e

    def fetch_one(
        self,
        sql: str,
        params: tuple | dict | None = None,
    ) -> dict[str, Any] | None:
        """خواندن یک سطر."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(
        self,
        sql: str,
        params: tuple | dict | None = None,
    ) -> list[dict[str, Any]]:
        """خواندن همه سطرها."""
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # === Lifecycle ===

    def close(self) -> None:
        """بستن همه اتصال‌های باز (در همه threadها)."""
        for conn in self._all_connections:
            try:
                conn.close()
            except Exception:
                pass
        self._all_connections = []
        if hasattr(self._local, "connection"):
            del self._local.connection
        logger.debug("همه اتصال‌های دیتابیس بسته شد")

    def __enter__(self) -> "Database":
        self.connect()
        # ⚠️ فقط اگه جدول courses نیست، init_schema
        try:
            row = self.connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='courses'"
            ).fetchone()
            if not row:
                self.init_schema()
        except Exception:
            pass
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Database(path={self.db_path})"