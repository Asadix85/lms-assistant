"""مدل Content (محتوای درس - PDF, ZIP, ...)."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import urlparse


@dataclass
class Content:
    """یک فایل محتوا در LMS."""

    id: str                          # hash از URL (unique)
    course_id: str                   # FK → Course
    title: str                       # "chapter01.pdf"
    url: str                         # URL کامل
    content_type: str                # "pdf", "zip", "docx", ...
    filename: str                    # "chapter01.pdf"
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("Content.url نمی‌تواند خالی باشد")
        if not self.course_id:
            raise ValueError("Content.course_id نمی‌تواند خالی باشد")

    @classmethod
    def from_url_and_title(
        cls,
        url: str,
        title: str,
        course_id: str,
    ) -> "Content":
        """ساخت Content از URL و عنوان.

        Args:
            url: URL کامل فایل
            title: متن لینک (مثلاً "chapter01.pdf")
            course_id: شناسه درس

        Returns:
            نمونه Content
        """
        # استخراج filename از URL
        parsed = urlparse(url)
        filename = PurePosixPath(parsed.path).name or title

        # استخراج پسوند
        ext = PurePosixPath(filename).suffix.lstrip(".").lower()
        if not ext:
            ext = "unknown"

        # ساخت ID از URL (یکتا)
        content_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

        return cls(
            id=content_id,
            course_id=course_id,
            title=title.strip() or filename,
            url=url,
            content_type=ext,
            filename=filename,
        )

    @property
    def size_human(self) -> str:
        """(اختیاری) نمایش انسانی از حجم."""
        return "?"  # فعلاً نمی‌دانیم

    def __repr__(self) -> str:
        return f"Content(id={self.id!r}, title={self.title!r}, type={self.content_type!r})"