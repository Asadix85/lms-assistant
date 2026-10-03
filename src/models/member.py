"""مدل Member (همکلاسی یا استاد)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemberType(str, Enum):
    """نوع عضو."""
    STUDENT = "student"
    TEACHER = "teacher"
    SUPPORT = "support"
    UNKNOWN = "unknown"


@dataclass
class Member:
    """یک عضو درس (استاد، همکلاسی، یا پشتیبان)."""

    id: str
    course_id: str
    name: str
    profile_url: str
    member_type: MemberType = MemberType.UNKNOWN
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Member.id نمی‌تواند خالی باشد")
        if not self.name:
            raise ValueError("Member.name نمی‌تواند خالی باشد")

    @property
    def is_teacher(self) -> bool:
        """آیا استاد است؟"""
        return self.member_type == MemberType.TEACHER

    @property
    def is_student(self) -> bool:
        """آیا دانشجو است؟"""
        return self.member_type == MemberType.STUDENT

    def __repr__(self) -> str:
        return f"Member(id={self.id!r}, name={self.name!r}, type={self.member_type.value!r})"