"""Repository برای Quera (scoped به user_id)."""

import json
from datetime import datetime

from loguru import logger

from src.models.quera_assignment import QueraAssignment, QueraProblem
from src.models.quera_course import QueraCourse
from src.storage.repositories.base import BaseRepository


class QueraAssignmentRepository(BaseRepository):
    TABLE_NAME = "quera_assignments"

    def save(self, a: QueraAssignment) -> None:
        data = self._to_dict(a)
        existing = self.db.fetch_one(
            "SELECT id FROM quera_assignments WHERE user_id = ? AND id = ?",
            (self.user_id, a.id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE quera_assignments SET
                    name = ?, course_name = ?, finish_time = ?,
                    problems_json = ?, problems_count = ?,
                    submitted_count = ?, last_seen_at = ?,
                    is_manual = ?, is_done = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    data["name"], data["course_name"], data["finish_time"],
                    data["problems_json"], data["problems_count"],
                    data["submitted_count"], data["last_seen_at"],
                    data["is_manual"], data["is_done"],
                    self.user_id, data["id"],
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO quera_assignments (
                    user_id, id, name, course_name, finish_time,
                    problems_json, problems_count, submitted_count,
                    is_new, is_manual, is_done, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["name"], data["course_name"],
                    data["finish_time"], data["problems_json"],
                    data["problems_count"], data["submitted_count"],
                    data["is_new"], data["is_manual"], data["is_done"],
                    data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج تمرین Quera جدید: {a.name[:40]}")

        self.db.connection.commit()

    def get_by_id(self, aid: str) -> QueraAssignment | None:
        row = self.db.fetch_one(
            "SELECT * FROM quera_assignments WHERE user_id = ? AND id = ?",
            (self.user_id, aid),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[QueraAssignment]:
        rows = self.db.fetch_all(
            "SELECT * FROM quera_assignments WHERE user_id = ? ORDER BY finish_time",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_upcoming(self, limit: int = 20) -> list[QueraAssignment]:
        now = datetime.now().isoformat()
        rows = self.db.fetch_all(
            "SELECT * FROM quera_assignments WHERE user_id = ? "
            "AND (finish_time IS NULL OR finish_time >= ?) "
            "ORDER BY finish_time LIMIT ?",
            (self.user_id, now, limit),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[QueraAssignment]:
        rows = self.db.fetch_all(
            "SELECT * FROM quera_assignments WHERE user_id = ? AND is_new = 1 "
            "ORDER BY finish_time",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def mark_all_seen(self) -> None:
        self.db.execute(
            "UPDATE quera_assignments SET is_new = 0 WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.connection.commit()

    def set_done(self, aid: str, done: bool = True) -> None:
        self.db.execute(
            "UPDATE quera_assignments SET is_done = ? WHERE user_id = ? AND id = ?",
            (1 if done else 0, self.user_id, aid),
        )
        self.db.connection.commit()

    def delete(self, aid: str) -> None:
        self.db.execute(
            "DELETE FROM quera_assignments WHERE user_id = ? AND id = ?",
            (self.user_id, aid),
        )
        self.db.connection.commit()

    def _to_dict(self, a: QueraAssignment) -> dict:
        problems_data = [
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "submission_score": p.submission_score,
                "state": p.state,
            }
            for p in a.problems
        ]
        return {
            "id": a.id,
            "name": a.name,
            "course_name": a.course_name,
            "finish_time": a.finish_time.isoformat() if a.finish_time else None,
            "problems_json": json.dumps(problems_data, ensure_ascii=False),
            "problems_count": a.problems_count,
            "submitted_count": a.submitted_count,
            "is_new": 0,
            "is_manual": 1 if a.is_manual else 0,
            "is_done": 1 if a.is_done else 0,
            "first_seen_at": a.first_seen_at.isoformat(),
            "last_seen_at": a.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> QueraAssignment:
        problems: list[QueraProblem] = []
        problems_json = row.get("problems_json")
        if problems_json:
            try:
                data = json.loads(problems_json)
                for p in data:
                    problems.append(
                        QueraProblem(
                            id=str(p.get("id", "")),
                            name=p.get("name", ""),
                            type=p.get("type", "U"),
                            submission_score=p.get("submission_score"),
                            state=p.get("state", "NO_SUBMIT"),
                        )
                    )
            except json.JSONDecodeError:
                pass

        return QueraAssignment(
            id=row["id"],
            name=row["name"],
            course_name=row.get("course_name", ""),
            finish_time=(
                datetime.fromisoformat(row["finish_time"])
                if row.get("finish_time")
                else None
            ),
            problems=problems,
            is_manual=bool(row.get("is_manual", 0)),
            is_done=bool(row.get("is_done", 0)),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )


class QueraCourseRepository(BaseRepository):
    TABLE_NAME = "quera_courses"

    def save(self, c: QueraCourse) -> None:
        existing = self.db.fetch_one(
            "SELECT id FROM quera_courses WHERE user_id = ? AND id = ?",
            (self.user_id, c.id),
        )
        if existing:
            self.db.execute(
                """
                UPDATE quera_courses SET
                    name = ?, url = ?, teacher = ?,
                    is_active = ?, assignments_count = ?,
                    last_seen_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    c.name, c.url, c.teacher,
                    1 if c.is_active else 0,
                    c.assignments_count,
                    c.last_seen_at.isoformat(),
                    self.user_id, c.id,
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO quera_courses (
                    user_id, id, name, url, teacher, is_active,
                    assignments_count, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    c.id, c.name, c.url, c.teacher,
                    1 if c.is_active else 0,
                    c.assignments_count,
                    c.first_seen_at.isoformat(),
                    c.last_seen_at.isoformat(),
                ),
            )
            logger.debug(f"درج کلاس Quera: {c.name[:40]}")
        self.db.connection.commit()

    def get_by_id(self, cid: str) -> QueraCourse | None:
        row = self.db.fetch_one(
            "SELECT * FROM quera_courses WHERE user_id = ? AND id = ?",
            (self.user_id, cid),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[QueraCourse]:
        rows = self.db.fetch_all(
            "SELECT * FROM quera_courses WHERE user_id = ? ORDER BY name",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_active(self) -> list[QueraCourse]:
        rows = self.db.fetch_all(
            "SELECT * FROM quera_courses WHERE user_id = ? AND is_active = 1 ORDER BY name",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def _from_dict(self, row: dict) -> QueraCourse:
        return QueraCourse(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            teacher=row.get("teacher", ""),
            is_active=bool(row.get("is_active", 1)),
            assignments_count=int(row.get("assignments_count") or 0),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
