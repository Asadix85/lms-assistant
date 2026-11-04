"""Repository برای CourseSchedule (scoped به user_id)."""

import json
from datetime import datetime

from loguru import logger

from src.models.course_schedule import ClassSession, CourseSchedule
from src.storage.repositories.base import BaseRepository


class CourseScheduleRepository(BaseRepository):
    TABLE_NAME = "course_schedules"

    def save(self, schedule: CourseSchedule) -> None:
        existing = self.db.fetch_one(
            "SELECT course_id FROM course_schedules WHERE user_id = ? AND course_id = ?",
            (self.user_id, schedule.course_id),
        )

        now = datetime.now().isoformat()
        sessions_data = [
            {
                "weekday": s.weekday,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "location": s.location,
            }
            for s in schedule.sessions
        ]
        sessions_json = json.dumps(sessions_data, ensure_ascii=False)

        if existing:
            self.db.execute(
                """
                UPDATE course_schedules SET
                    course_code = ?, sessions_json = ?,
                    raw_text = ?, last_seen_at = ?
                WHERE user_id = ? AND course_id = ?
                """,
                (
                    schedule.course_code, sessions_json,
                    schedule.raw_text, now,
                    self.user_id, schedule.course_id,
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO course_schedules (
                    user_id, course_id, course_code, sessions_json,
                    raw_text, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    schedule.course_id, schedule.course_code,
                    sessions_json, schedule.raw_text, now, now,
                ),
            )
            logger.debug(f"درج برنامه‌ی جدید: {schedule.course_id}")

        self.db.connection.commit()

    def get_by_id(self, course_id: str) -> CourseSchedule | None:
        row = self.db.fetch_one(
            "SELECT * FROM course_schedules WHERE user_id = ? AND course_id = ?",
            (self.user_id, course_id),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[CourseSchedule]:
        rows = self.db.fetch_all(
            "SELECT * FROM course_schedules WHERE user_id = ?",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def _from_dict(self, row: dict) -> CourseSchedule:
        sessions = []
        try:
            data = json.loads(row.get("sessions_json") or "[]")
            for s in data:
                sessions.append(
                    ClassSession(
                        weekday=s.get("weekday", ""),
                        start_time=s.get("start_time", ""),
                        end_time=s.get("end_time", ""),
                        location=s.get("location", ""),
                    )
                )
        except json.JSONDecodeError:
            pass

        return CourseSchedule(
            course_id=row["course_id"],
            course_code=row.get("course_code", ""),
            sessions=sessions,
            raw_text=row.get("raw_text", ""),
        )
