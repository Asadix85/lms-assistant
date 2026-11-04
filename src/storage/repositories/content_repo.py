"""Repository برای Content (scoped به user_id)."""

from datetime import datetime

from loguru import logger

from src.models.content import Content
from src.storage.repositories.base import BaseRepository


class ContentRepository(BaseRepository):
    TABLE_NAME = "contents"

    def save(self, content: Content) -> None:
        data = self._to_dict(content)
        existing = self.db.fetch_one(
            "SELECT id FROM contents WHERE user_id = ? AND id = ?",
            (self.user_id, content.id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE contents SET
                    title = ?, url = ?, content_type = ?, filename = ?,
                    last_seen_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    data["title"], data["url"], data["content_type"],
                    data["filename"], data["last_seen_at"],
                    self.user_id, data["id"],
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO contents (
                    user_id, id, course_id, title, url, content_type, filename,
                    is_new, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["course_id"], data["title"], data["url"],
                    data["content_type"], data["filename"], data["is_new"],
                    data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج محتوای جدید: {content.title}")

        self.db.connection.commit()

    def save_many(self, contents: list[Content]) -> None:
        for c in contents:
            self.save(c)

    def get_by_id(self, content_id: str) -> Content | None:
        row = self.db.fetch_one(
            "SELECT * FROM contents WHERE user_id = ? AND id = ?",
            (self.user_id, content_id),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Content]:
        rows = self.db.fetch_all(
            "SELECT * FROM contents WHERE user_id = ? ORDER BY title",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str) -> list[Content]:
        rows = self.db.fetch_all(
            "SELECT * FROM contents WHERE user_id = ? AND course_id = ? ORDER BY title",
            (self.user_id, course_id),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[Content]:
        rows = self.db.fetch_all(
            "SELECT * FROM contents WHERE user_id = ? AND is_new = 1 ORDER BY first_seen_at",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def mark_all_seen(self) -> None:
        self.db.execute(
            "UPDATE contents SET is_new = 0 WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.connection.commit()

    def _to_dict(self, c: Content) -> dict:
        return {
            "id": c.id,
            "course_id": c.course_id,
            "title": c.title,
            "url": c.url,
            "content_type": c.content_type,
            "filename": c.filename,
            "is_new": 0,
            "first_seen_at": c.first_seen_at.isoformat(),
            "last_seen_at": c.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Content:
        return Content(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            url=row["url"],
            content_type=row["content_type"],
            filename=row["filename"],
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
