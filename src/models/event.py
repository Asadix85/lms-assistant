"""مدل Event (رویداد LMS: جلسه آنلاین، آزمون، ددلاین)."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """نوع رویداد."""
    LIVE_SESSION = "live_session"    # جلسه آنلاین (jaam)
    EXAM = "exam"                    # آزمون
    DEADLINE = "deadline"            # مهلت
    ANNOUNCEMENT = "announcement"    # اطلاعیه
    UNKNOWN = "unknown"


@dataclass
class Event:
    """یک رویداد LMS."""

    id: str
    course_id: str | None            # می‌تواند None باشد (اگر درس مشخص نیست)
    title: str
    event_type: EventType
    url: str | None = None
    room_token: str | None = None    # توکن jaam/joinfast
    start_at: datetime | None = None
    end_at: datetime | None = None
    description: str | None = None
    is_new: bool = True
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("Event.title نمی‌تواند خالی باشد")

    @classmethod
    def from_joinfast(
        cls,
        url: str,
        title: str,
        start_hour: str | None = None,
        course_id: str | None = None,
    ) -> "Event":
        """ساخت Event از لینک joinfast.

        Args:
            url: /jaam/joinfast/{token}/{id}
            title: متن لینک (مثل "ساختمان داده 03-جلسه 3")
            start_hour: مثل "11:00"
            course_id: شناسه درس (اگر می‌دانیم)
        """
        # استخراج توکن از URL
        token = None
        parts = url.split("/")
        if "joinfast" in parts:
            idx = parts.index("joinfast")
            if idx + 1 < len(parts):
                token = parts[idx + 1]

        # ID از URL
        event_id = hashlib.sha256(url.encode()).hexdigest()[:16]

        # شروع
        start_at = None
        if start_hour:
            try:
                h, m = start_hour.split(":")
                today = datetime.now()
                start_at = today.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
            except (ValueError, AttributeError):
                pass

        return cls(
            id=event_id,
            course_id=course_id,
            title=title.strip(),
            event_type=EventType.LIVE_SESSION,
            url=url,
            room_token=token,
            start_at=start_at,
        )

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id!r}, title={self.title!r}, "
            f"type={self.event_type.value!r})"
        )