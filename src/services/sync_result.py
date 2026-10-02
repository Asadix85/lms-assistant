"""نتیجه Sync."""

from dataclasses import dataclass, field

from src.models.change import Change


@dataclass
class SyncResult:
    """نتیجه‌ی یک Sync کامل."""

    is_first_sync: bool = False

    # Courses
    courses_new: int = 0
    courses_updated: int = 0
    courses_removed: int = 0

    # Contents
    contents_new: int = 0
    contents_updated: int = 0
    contents_removed: int = 0

    # Events
    events_new: int = 0
    events_updated: int = 0
    events_removed: int = 0

    # Posts
    posts_new: int = 0
    posts_updated: int = 0
    posts_removed: int = 0

    # Assignments
    assignments_new: int = 0
    assignments_updated: int = 0
    assignments_removed: int = 0

    changes: list[Change] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: str | None = None

    @property
    def total_new(self) -> int:
        return (
            self.courses_new
            + self.contents_new
            + self.events_new
            + self.posts_new
            + self.assignments_new
        )

    @property
    def total_updated(self) -> int:
        return (
            self.courses_updated
            + self.contents_updated
            + self.events_updated
            + self.posts_updated
            + self.assignments_updated
        )

    @property
    def total_removed(self) -> int:
        return (
            self.courses_removed
            + self.contents_removed
            + self.events_removed
            + self.posts_removed
            + self.assignments_removed
        )

    @property
    def has_changes(self) -> bool:
        return self.total_new > 0 or self.total_updated > 0

    @property
    def has_error(self) -> bool:
        return self.error is not None

    def summary(self) -> str:
        if self.is_first_sync:
            return (
                f"🎉 اولین Sync: "
                f"{self.courses_new} درس، "
                f"{self.contents_new} فایل، "
                f"{self.events_new} رویداد، "
                f"{self.posts_new} پست، "
                f"{self.assignments_new} تکلیف"
            )

        if not self.has_changes:
            return "✨ هیچ تغییر جدیدی نیست"

        parts = []
        if self.courses_new:
            parts.append(f"{self.courses_new} درس")
        if self.contents_new:
            parts.append(f"{self.contents_new} فایل")
        if self.events_new:
            parts.append(f"{self.events_new} رویداد")
        if self.posts_new:
            parts.append(f"{self.posts_new} پست")
        if self.assignments_new:
            parts.append(f"{self.assignments_new} تکلیف")

        if not parts:
            return f"🔄 {self.total_updated} به‌روزرسانی"

        return "📢 " + "، ".join(parts) + " جدید"

    def __repr__(self) -> str:
        return (
            f"SyncResult(first={self.is_first_sync}, "
            f"new={self.total_new}, "
            f"updated={self.total_updated})"
        )