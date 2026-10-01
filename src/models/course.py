"""مدل Course."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CourseStatus(str, Enum):
    """وضعیت درس."""
    ACTIVE = "active"
    FINISHED = "finished"
    UNKNOWN = "unknown"


@dataclass
class Course:
    """یک درس در LMS.

    Attributes:
        id: شناسه گروه (group_id)
        name: نام درس
        url: URL کامل درس
        group_id: شناسه گروه
        domain: دامنه‌ی درس ("lms3", "lms4", "lms5")
        nodeg_url: لینک nodeg (اگر درس در دامنه‌ی دیگر باشد)
        teacher: نام استاد
        code: کد درس (مثل "36-20-028")
        term: ترم (مثل "04")
        status: وضعیت درس
        first_seen_at: اولین بار که دیدیم
        last_seen_at: آخرین بار که دیدیم
    """

    id: str
    name: str
    url: str
    group_id: str
    domain: str = "lms4"
    nodeg_url: str | None = None
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
        if self.domain not in ("lms3", "lms4", "lms5"):
            raise ValueError(f"دامنه نامعتبر: {self.domain}")

    @property
    def is_active(self) -> bool:
        """آیا درس در ترم جاری است؟"""
        return self.status == CourseStatus.ACTIVE

    @property
    def is_cross_domain(self) -> bool:
        """آیا درس در دامنه‌ی دیگری است؟"""
        return self.nodeg_url is not None

    def __repr__(self) -> str:
        return (
            f"Course(id={self.id!r}, name={self.name!r}, "
            f"domain={self.domain!r}, status={self.status.value!r})"
        )