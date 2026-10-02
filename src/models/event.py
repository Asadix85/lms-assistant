"""مدل Event (رویداد LMS: جلسه آنلاین، آزمون، ددلاین)."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """نوع رویداد."""
    LIVE_SESSION = "live_session"
    EXAM = "exam"
    DEADLINE = "deadline"
    ANNOUNCEMENT = "announcement"
    UNKNOWN = "unknown"


@dataclass
class Event:
    """یک رویداد LMS."""

    id: str
    course_id: str | None = None
    title: str = ""
    event_type: EventType = EventType.UNKNOWN
    url: str | None = None
    room_token: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    description: str | None = None
    is_new: bool = True
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Event.id نمی‌تواند خالی باشد")
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

        ID پایدار: از آخرین بخش URL (room_id) استفاده می‌کنیم.
        مثال: /jaam/joinfast/{token}/{room_id} → id = "room_id"
        """
        # استخراج توکن و room_id
        token = None
        room_id = None
        parts = url.rstrip("/").split("/")
        if "joinfast" in parts:
            idx = parts.index("joinfast")
            if idx + 1 < len(parts):
                token = parts[idx + 1]
            if idx + 2 < len(parts):
                room_id = parts[idx + 2]

        # ID پایدار: بر اساس room_id (نه URL که توکن داره)
        if room_id:
            event_id = f"jaam_{room_id}"
        else:
            # fallback: hash کل URL
            event_id = hashlib.sha256(url.encode()).hexdigest()[:16]

        # شروع
        start_at = None
        if start_hour:
            try:
                h, m = start_hour.split(":")
                today = datetime.now()
                start_at = today.replace(
                    hour=int(h), minute=int(m), second=0, microsecond=0
                )
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