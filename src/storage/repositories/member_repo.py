"""Repository برای Member (scoped به user_id)."""

from datetime import datetime

from loguru import logger

from src.models.member import Member, MemberType
from src.storage.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    TABLE_NAME = "members"

    def save(self, member: Member) -> None:
        data = self._to_dict(member)
        existing = self.db.fetch_one(
            "SELECT id FROM members WHERE user_id = ? AND id = ? AND course_id = ?",
            (self.user_id, member.id, member.course_id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE members SET
                    name = ?, profile_url = ?, member_type = ?,
                    last_seen_at = ?
                WHERE user_id = ? AND id = ? AND course_id = ?
                """,
                (
                    data["name"], data["profile_url"], data["member_type"],
                    data["last_seen_at"],
                    self.user_id, data["id"], data["course_id"],
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO members (
                    user_id, id, course_id, name, profile_url, member_type,
                    first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["course_id"], data["name"],
                    data["profile_url"], data["member_type"],
                    data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج عضو جدید: {member.name}")

        self.db.connection.commit()

    def get_by_id(self, member_id: str) -> Member | None:
        row = self.db.fetch_one(
            "SELECT * FROM members WHERE user_id = ? AND id = ? LIMIT 1",
            (self.user_id, member_id),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Member]:
        rows = self.db.fetch_all(
            "SELECT * FROM members WHERE user_id = ? ORDER BY name",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str) -> list[Member]:
        rows = self.db.fetch_all(
            "SELECT * FROM members WHERE user_id = ? AND course_id = ? "
            "ORDER BY CASE member_type "
            "WHEN 'teacher' THEN 1 "
            "WHEN 'support' THEN 2 "
            "WHEN 'student' THEN 3 "
            "ELSE 4 END, name",
            (self.user_id, course_id),
        )
        return [self._from_dict(r) for r in rows]

    def get_students(self, course_id: str) -> list[Member]:
        rows = self.db.fetch_all(
            "SELECT * FROM members WHERE user_id = ? AND course_id = ? "
            "AND member_type = 'student' ORDER BY name",
            (self.user_id, course_id),
        )
        return [self._from_dict(r) for r in rows]

    def get_teachers(self, course_id: str) -> list[Member]:
        rows = self.db.fetch_all(
            "SELECT * FROM members WHERE user_id = ? AND course_id = ? "
            "AND member_type = 'teacher' ORDER BY name",
            (self.user_id, course_id),
        )
        return [self._from_dict(r) for r in rows]

    def _to_dict(self, m: Member) -> dict:
        return {
            "id": m.id,
            "course_id": m.course_id,
            "name": m.name,
            "profile_url": m.profile_url,
            "member_type": m.member_type.value,
            "first_seen_at": m.first_seen_at.isoformat(),
            "last_seen_at": m.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Member:
        if "member_type" in row and row["member_type"]:
            member_type = MemberType(row["member_type"])
        elif "is_teacher" in row:
            is_teacher = bool(row.get("is_teacher", 0))
            member_type = MemberType.TEACHER if is_teacher else MemberType.STUDENT
        else:
            member_type = MemberType.UNKNOWN

        return Member(
            id=row["id"],
            course_id=row["course_id"],
            name=row["name"],
            profile_url=row["profile_url"],
            member_type=member_type,
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
