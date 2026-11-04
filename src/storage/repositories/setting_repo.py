"""Repository برای Settings (scoped به user_id)."""

from datetime import datetime


class SettingRepository:
    def __init__(self, db, user_id: str | None = None) -> None:
        self.db = db
        self.user_id = user_id or "__local__"

    def set(self, key: str, value: str) -> None:
        now = datetime.now().isoformat()
        self.db.execute(
            """
            INSERT INTO settings (user_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (self.user_id, key, value, now),
        )
        self.db.connection.commit()

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.db.fetch_one(
            "SELECT value FROM settings WHERE user_id = ? AND key = ?",
            (self.user_id, key),
        )
        return row["value"] if row else default

    def delete(self, key: str) -> None:
        self.db.execute(
            "DELETE FROM settings WHERE user_id = ? AND key = ?",
            (self.user_id, key),
        )
        self.db.connection.commit()

    def get_all(self) -> dict[str, str]:
        rows = self.db.fetch_all(
            "SELECT key, value FROM settings WHERE user_id = ?",
            (self.user_id,),
        )
        return {r["key"]: r["value"] for r in rows}
