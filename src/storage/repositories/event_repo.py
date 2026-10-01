"""Repository برای Event."""

from datetime import datetime

from loguru import logger

from src.models.event import Event, EventType
from src.storage.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    """ذخیره و بازیابی Event."""

    TABLE_NAME = "events"

    def save(self, event: Event) -> None:
        data = self._to_dict(event)
        existing = self.db.fetch_one(
            "SELECT id FROM events WHERE id = ?",
            (event.id,),
        )

        if existing:
            self.db.execute(
                """
                UPDATE events SET
                    title = ?, url = ?, start_at = ?, last_seen_at = ?
                WHERE id = ?
                """,
                (data["title"], data["url"], data["start_at"],
                 data["last_seen_at"], data["id"]),
            )
        else:
            self.db.execute(
                """
                INSERT INTO events (
                    id, course_id, title, event_type, url, room_token,
                    start_at, end_at, description,
                    is_new, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"], data["course_id"], data["title"],
                    data["event_type"], data["url"], data["room_token"],
                    data["start_at"], data["end_at"], data["description"],
                    data["is_new"], data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج رویداد جدید: {event.title}")

        self.db.connection.commit()

    def get_by_id(self, event_id: str) -> Event | None:
        row = self.db.fetch_one("SELECT * FROM events WHERE id = ?", (event_id,))
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Event]:
        rows = self.db.fetch_all("SELECT * FROM events ORDER BY start_at")
        return [self._from_dict(r) for r in rows]

    def get_upcoming(self, limit: int = 10) -> list[Event]:
        """رویدادهای آینده."""
        now = datetime.now().isoformat()
        rows = self.db.fetch_all(
            "SELECT * FROM events WHERE start_at >= ? ORDER BY start_at LIMIT ?",
            (now, limit),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str) -> list[Event]:
        rows = self.db.fetch_all(
            "SELECT * FROM events WHERE course_id = ? ORDER BY start_at",
            (course_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[Event]:
        rows = self.db.fetch_all(
            "SELECT * FROM events WHERE is_new = 1 ORDER BY start_at"
        )
        return [self._from_dict(r) for r in rows]

    def mark_all_seen(self) -> None:
        self.db.execute("UPDATE events SET is_new = 0")
        self.db.connection.commit()

    # === Helpers ===

    def _to_dict(self, e: Event) -> dict:
        return {
            "id": e.id,
            "course_id": e.course_id,
            "title": e.title,
            "event_type": e.event_type.value,
            "url": e.url,
            "room_token": e.room_token,
            "start_at": e.start_at.isoformat() if e.start_at else None,
            "end_at": e.end_at.isoformat() if e.end_at else None,
            "description": e.description,
            "is_new": 0,
            "first_seen_at": e.first_seen_at.isoformat(),
            "last_seen_at": e.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Event:
        return Event(
            id=row["id"],
            course_id=row.get("course_id"),
            title=row["title"],
            event_type=EventType(row["event_type"]) if row.get("event_type") else EventType.UNKNOWN,
            url=row.get("url"),
            room_token=row.get("room_token"),
            start_at=datetime.fromisoformat(row["start_at"]) if row.get("start_at") else None,
            end_at=datetime.fromisoformat(row["end_at"]) if row.get("end_at") else None,
            description=row.get("description"),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )