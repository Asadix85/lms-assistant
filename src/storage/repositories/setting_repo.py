"""Repository برای Settings."""

from datetime import datetime


class SettingRepository:
    """ذخیره و بازیابی تنظیمات."""

    def __init__(self, db) -> None:
        self.db = db

    def set(self, key: str, value: str) -> None:
        """ذخیره یک تنظیم."""
        now = datetime.now().isoformat()
        self.db.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )
        self.db.connection.commit()

    def get(self, key: str, default: str | None = None) -> str | None:
        """خواندن یک تنظیم."""
        row = self.db.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def delete(self, key: str) -> None:
        """حذف یک تنظیم."""
        self.db.execute("DELETE FROM settings WHERE key = ?", (key,))
        self.db.connection.commit()

    def get_all(self) -> dict[str, str]:
        """همه تنظیمات."""
        rows = self.db.fetch_all("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in rows}