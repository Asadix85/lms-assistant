"""Repository برای Assignment (scoped به user_id)."""

from datetime import datetime

from loguru import logger

from src.models.assignment import Assignment
from src.storage.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository):
    TABLE_NAME = "assignments"

    def save(self, a: Assignment) -> None:
        data = self._to_dict(a)
        existing = self.db.fetch_one(
            "SELECT id FROM assignments WHERE user_id = ? AND id = ?",
            (self.user_id, a.id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE assignments SET
                    title = ?, description = ?, deadline = ?,
                    response_count = ?, last_seen_at = ?,
                    is_manual = ?, is_done = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    data["title"], data["description"], data["deadline"],
                    data["response_count"], data["last_seen_at"],
                    data["is_manual"], data["is_done"],
                    self.user_id, data["id"],
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO assignments (
                    user_id, id, course_id, title, description, post_id,
                    start_at, deadline, start_at_jalali, deadline_jalali,
                    submit_url, view_url, response_count,
                    is_new, is_manual, is_done, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["course_id"], data["title"],
                    data["description"], data["post_id"], data["start_at"],
                    data["deadline"], data["start_at_jalali"],
                    data["deadline_jalali"], data["submit_url"],
                    data["view_url"], data["response_count"],
                    data["is_new"], data["is_manual"], data["is_done"],
                    data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج تکلیف جدید: {a.title[:40]}")

        self.db.connection.commit()

    def get_by_id(self, aid: str) -> Assignment | None:
        row = self.db.fetch_one(
            "SELECT * FROM assignments WHERE user_id = ? AND id = ?",
            (self.user_id, aid),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Assignment]:
        rows = self.db.fetch_all(
            "SELECT * FROM assignments WHERE user_id = ? ORDER BY deadline",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str) -> list[Assignment]:
        rows = self.db.fetch_all(
            "SELECT * FROM assignments WHERE user_id = ? AND course_id = ? ORDER BY deadline",
            (self.user_id, course_id),
        )
        return [self._from_dict(r) for r in rows]

    def get_upcoming(self, limit: int = 10) -> list[Assignment]:
        now = datetime.now().isoformat()
        rows = self.db.fetch_all(
            "SELECT * FROM assignments WHERE user_id = ? AND deadline >= ? "
            "ORDER BY deadline LIMIT ?",
            (self.user_id, now, limit),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[Assignment]:
        rows = self.db.fetch_all(
            "SELECT * FROM assignments WHERE user_id = ? AND is_new = 1 ORDER BY deadline",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def mark_all_seen(self) -> None:
        self.db.execute(
            "UPDATE assignments SET is_new = 0 WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.connection.commit()

    def set_done(self, aid: str, done: bool = True) -> None:
        self.db.execute(
            "UPDATE assignments SET is_done = ? WHERE user_id = ? AND id = ?",
            (1 if done else 0, self.user_id, aid),
        )
        self.db.connection.commit()

    def delete(self, aid: str) -> None:
        self.db.execute(
            "DELETE FROM assignments WHERE user_id = ? AND id = ?",
            (self.user_id, aid),
        )
        self.db.connection.commit()

    def _to_dict(self, a: Assignment) -> dict:
        return {
            "id": a.id,
            "course_id": a.course_id,
            "title": a.title,
            "description": a.description,
            "post_id": a.post_id,
            "start_at": a.start_at.isoformat() if a.start_at else None,
            "deadline": a.deadline.isoformat() if a.deadline else None,
            "start_at_jalali": a.start_at_jalali,
            "deadline_jalali": a.deadline_jalali,
            "submit_url": a.submit_url,
            "view_url": a.view_url,
            "response_count": a.response_count,
            "is_new": 1 if a.is_new else 0,
            "is_manual": 1 if a.is_manual else 0,
            "is_done": 1 if a.is_done else 0,
            "first_seen_at": a.first_seen_at.isoformat(),
            "last_seen_at": a.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Assignment:
        return Assignment(
            id=row["id"],
            course_id=row["course_id"],
            title=row["title"],
            description=row.get("description") or "",
            post_id=row.get("post_id"),
            start_at=datetime.fromisoformat(row["start_at"]) if row.get("start_at") else None,
            deadline=datetime.fromisoformat(row["deadline"]) if row.get("deadline") else None,
            start_at_jalali=row.get("start_at_jalali"),
            deadline_jalali=row.get("deadline_jalali"),
            submit_url=row.get("submit_url"),
            view_url=row.get("view_url"),
            response_count=int(row.get("response_count") or 0),
            is_new=bool(row.get("is_new", 0)),
            is_manual=bool(row.get("is_manual", 0)),
            is_done=bool(row.get("is_done", 0)),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
