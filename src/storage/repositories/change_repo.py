"""Repository برای Change."""

import json
from datetime import datetime

from src.models.change import Change, ChangeType, EntityType
from src.storage.repositories.base import BaseRepository


class ChangeRepository(BaseRepository):
    """ذخیره و بازیابی Change."""

    TABLE_NAME = "changes"

    def save(self, change: Change) -> None:
        """ذخیره یک تغییر."""
        self.db.execute(
            """
            INSERT INTO changes (
                type, entity_type, entity_id, course_id, data, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                change.type.value,
                change.entity_type.value,
                change.entity_id,
                change.course_id,
                json.dumps(change.data, ensure_ascii=False) if change.data else None,
                change.detected_at.isoformat(),
            ),
        )
        self.db.connection.commit()

    def save_many(self, changes: list[Change]) -> None:
        """ذخیره چند تغییر."""
        for c in changes:
            self.save(c)

    def get_all(self, limit: int = 100) -> list[Change]:
        rows = self.db.fetch_all(
            "SELECT * FROM changes ORDER BY detected_at DESC LIMIT ?",
            (limit,),
        )
        return [self._from_dict(r) for r in rows]

    def get_recent(self, limit: int = 20) -> list[Change]:
        return self.get_all(limit=limit)

    def get_by_entity(self, entity_id: str) -> list[Change]:
        rows = self.db.fetch_all(
            "SELECT * FROM changes WHERE entity_id = ? ORDER BY detected_at DESC",
            (entity_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str) -> list[Change]:
        rows = self.db.fetch_all(
            "SELECT * FROM changes WHERE course_id = ? ORDER BY detected_at DESC",
            (course_id,),
        )
        return [self._from_dict(r) for r in rows]

    def delete_all(self) -> None:
        """پاک کردن همه تغییرات."""
        self.db.execute("DELETE FROM changes")
        self.db.connection.commit()

    def get_by_id(self, item_id: str) -> Change | None:
        """BaseRepository این را می‌خواهد (ولی ما ID نداریم)."""
        return None

    def _from_dict(self, row: dict) -> Change:
        return Change(
            type=ChangeType(row["type"]),
            entity_type=EntityType(row["entity_type"]),
            entity_id=row["entity_id"],
            course_id=row.get("course_id"),
            data=json.loads(row["data"]) if row.get("data") else {},
            detected_at=datetime.fromisoformat(row["detected_at"]),
        )