"""Database wrapper برای SQLite."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from loguru import logger

from src.core.exceptions import StorageError


class Database:
    """مدیریت اتصال و عملیات SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    # === Connection ===

    def connect(self) -> sqlite3.Connection:
        """اتصال به دیتابیس (اگر نبود، می‌سازد)."""
        if self._connection is None:
            # اطمینان از وجود پوشه
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._connection = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            logger.debug(f"اتصال به دیتابیس: {self.db_path}")

        return self._connection

    @property
    def connection(self) -> sqlite3.Connection:
        """دسترسی به اتصال."""
        if self._connection is None:
            return self.connect()
        return self._connection

    # === Init ===

    def init_schema(self, schema_path: str | Path | None = None) -> None:
        """ساخت جداول از فایل schema.sql."""
        if schema_path is None:
            schema_path = Path(__file__).parent / "schema.sql"

        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise StorageError(f"فایل schema پیدا نشد: {schema_path}")

        schema = schema_path.read_text(encoding="utf-8")

        try:
            self.connection.executescript(schema)
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
        """بستن اتصال."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.debug("دیتابیس بسته شد")

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Database(path={self.db_path})"