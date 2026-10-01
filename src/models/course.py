"""مدل Course."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# === Enum اول تعریف شود ===
class CourseStatus(str, Enum):
    """وضعیت درس."""
    ACTIVE = "active"          # ترم جاری
    FINISHED = "finished"      # ترم پایان یافته
    UNKNOWN = "unknown"


# === بعد dataclass ===
@dataclass
class Course:
    """یک درس در LMS."""

    id: str
    name: str
    url: str
    group_id: str
    teacher: str | None = None
    code: str | None = None
    term: str | None = None
    status: CourseStatus = CourseStatus.UNKNOWN
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.id = self.id.strip()
        self.group_id = self.group_id.strip()
        if not self.id:
            raise ValueError("Course.id نمی‌تواند خالی باشد")
        if not self.name:
            raise ValueError("Course.name نمی‌تواند خالی باشد")

    @property
    def is_active(self) -> bool:
        """آیا درس در ترم جاری است؟"""
        return self.status == CourseStatus.ACTIVE

    def __repr__(self) -> str:
        return f"Course(id={self.id!r}, name={self.name!r}, status={self.status.value!r})"