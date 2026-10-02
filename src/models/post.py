"""مدل Post (پیام wall درس)."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Post:
    """پیام wall درس (از استاد یا همکلاسی)."""

    id: str
    course_id: str
    author: str
    author_id: str
    text: str
    posted_at: datetime | None = None
    posted_at_jalali: str | None = None
    post_url: str | None = None
    is_new: bool = True
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Post.id نمی‌تواند خالی باشد")
        if not self.text:
            raise ValueError("Post.text نمی‌تواند خالی باشد")

    @classmethod
    def make_id(cls, post_url: str, course_id: str) -> str:
        """ساخت ID پایدار از URL."""
        content = f"{course_id}:{post_url}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        return f"Post(id={self.id!r}, author={self.author!r}, text={self.text[:30]!r})"