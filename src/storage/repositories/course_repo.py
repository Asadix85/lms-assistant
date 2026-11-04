"""Repository برای Course (scoped به user_id)."""

from datetime import datetime

from loguru import logger

from src.models.course import Course, CourseStatus
from src.storage.repositories.base import BaseRepository


class CourseRepository(BaseRepository):
    TABLE_NAME = "courses"

    def save(self, course: Course) -> None:
        data = self._to_dict(course)
        existing = self.db.fetch_one(
            "SELECT id FROM courses WHERE user_id = ? AND id = ?",
            (self.user_id, course.id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE courses SET
                    name = ?, url = ?, group_id = ?, domain = ?,
                    nodeg_url = ?, teacher = ?, code = ?, term = ?,
                    status = ?, last_seen_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    data["name"], data["url"], data["group_id"], data["domain"],
                    data["nodeg_url"], data["teacher"], data["code"], data["term"],
                    data["status"], data["last_seen_at"],
                    self.user_id, data["id"],
                ),
            )
            logger.debug(f"به‌روزرسانی درس: {course.name}")
        else:
            self.db.execute(
                """
                INSERT INTO courses (
                    user_id, id, name, url, group_id, domain, nodeg_url,
                    teacher, code, term, status,
                    is_new, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["name"], data["url"], data["group_id"],
                    data["domain"], data["nodeg_url"], data["teacher"],
                    data["code"], data["term"], data["status"],
                    data["is_new"], data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج درس جدید: {course.name}")

        self.db.connection.commit()

    def get_by_id(self, course_id: str) -> Course | None:
        row = self.db.fetch_one(
            "SELECT * FROM courses WHERE user_id = ? AND id = ?",
            (self.user_id, course_id),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Course]:
        rows = self.db.fetch_all(
            "SELECT * FROM courses WHERE user_id = ? ORDER BY name",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_domain(self, domain: str) -> list[Course]:
        rows = self.db.fetch_all(
            "SELECT * FROM courses WHERE user_id = ? AND domain = ? ORDER BY name",
            (self.user_id, domain),
        )
        return [self._from_dict(r) for r in rows]

    def get_active(self) -> list[Course]:
        rows = self.db.fetch_all(
            "SELECT * FROM courses WHERE user_id = ? AND status = 'active' ORDER BY name",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[Course]:
        rows = self.db.fetch_all(
            "SELECT * FROM courses WHERE user_id = ? AND is_new = 1 ORDER BY first_seen_at",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def mark_seen(self, course_id: str) -> None:
        self.db.execute(
            "UPDATE courses SET is_new = 0 WHERE user_id = ? AND id = ?",
            (self.user_id, course_id),
        )
        self.db.connection.commit()

    def mark_all_seen(self) -> None:
        self.db.execute(
            "UPDATE courses SET is_new = 0 WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.connection.commit()

    def _to_dict(self, c: Course) -> dict:
        return {
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "group_id": c.group_id,
            "domain": c.domain,
            "nodeg_url": c.nodeg_url,
            "teacher": c.teacher,
            "code": c.code,
            "term": c.term,
            "status": c.status.value,
            "is_new": 0,
            "first_seen_at": c.first_seen_at.isoformat(),
            "last_seen_at": c.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Course:
        return Course(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            group_id=row["group_id"],
            domain=row["domain"],
            nodeg_url=row.get("nodeg_url"),
            teacher=row.get("teacher"),
            code=row.get("code"),
            term=row.get("term"),
            status=CourseStatus(row["status"]) if row.get("status") else CourseStatus.UNKNOWN,
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
