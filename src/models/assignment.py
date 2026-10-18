"""مدل Assignment (تکلیف)."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Assignment:
    """تکلیف درس."""

    id: str
    course_id: str
    title: str
    description: str = ""
    post_id: str | None = None
    start_at: datetime | None = None
    deadline: datetime | None = None
    start_at_jalali: str | None = None
    deadline_jalali: str | None = None
    submit_url: str | None = None
    view_url: str | None = None
    response_count: int = 0
    is_new: bool = True
    is_manual: bool = False
    is_done: bool = False
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Assignment.id نمی‌تواند خالی باشد")
        if not self.title:
            raise ValueError("Assignment.title نمی‌تواند خالی باشد")

    @property
    def has_deadline(self) -> bool:
        return self.deadline is not None

    @property
    def is_expired(self) -> bool:
        if not self.deadline:
            return False
        return datetime.now() > self.deadline

    def __repr__(self) -> str:
        return f"Assignment(id={self.id!r}, title={self.title[:30]!r})"