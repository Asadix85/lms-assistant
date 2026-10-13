"""Repository برای CourseSchedule."""

from datetime import datetime

from loguru import logger

from src.models.course_schedule import CourseSchedule
from src.storage.repositories.base import BaseRepository


class CourseScheduleRepository(BaseRepository):
    """ذخیره و بازیابی CourseSchedule."""

    TABLE_NAME = "course_schedules"

    def save(self, schedule: CourseSchedule) -> None:
        existing = self.db.fetch_one(
            "SELECT course_id FROM course_schedules WHERE course_id = ?",
            (schedule.course_id,),
        )

        now = datetime.now().isoformat()

        if existing:
            self.db.execute(
                """
                UPDATE course_schedules SET
                    weekday = ?, start_time = ?, end_time = ?,
                    building = ?, floor = ?, room = ?,
                    raw_text = ?, last_seen_at = ?
                WHERE course_id = ?
                """,
                (
                    schedule.weekday, schedule.start_time, schedule.end_time,
                    schedule.building, schedule.floor, schedule.room,
                    schedule.raw_text, now, schedule.course_id,
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO course_schedules (
                    course_id, weekday, start_time, end_time,
                    building, floor, room, raw_text,
                    first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule.course_id, schedule.weekday,
                    schedule.start_time, schedule.end_time,
                    schedule.building, schedule.floor, schedule.room,
                    schedule.raw_text, now, now,
                ),
            )
            logger.debug(f"درج برنامه‌ی جدید: {schedule.course_id}")

        self.db.connection.commit()

    def get_by_id(self, course_id: str) -> CourseSchedule | None:
        row = self.db.fetch_one(
            "SELECT * FROM course_schedules WHERE course_id = ?",
            (course_id,),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[CourseSchedule]:
        rows = self.db.fetch_all("SELECT * FROM course_schedules")
        return [self._from_dict(r) for r in rows]

    def _from_dict(self, row: dict) -> CourseSchedule:
        return CourseSchedule(
            course_id=row["course_id"],
            weekday=row.get("weekday"),
            start_time=row.get("start_time"),
            end_time=row.get("end_time"),
            building=row.get("building"),
            floor=row.get("floor"),
            room=row.get("room"),
            raw_text=row.get("raw_text", ""),
        )