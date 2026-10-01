"""نتیجه Sync."""

from dataclasses import dataclass, field

from src.models.change import Change


@dataclass
class SyncResult:
    """نتیجه‌ی یک Sync کامل."""

    is_first_sync: bool = False
    courses_new: int = 0
    courses_updated: int = 0
    courses_removed: int = 0
    contents_new: int = 0
    contents_updated: int = 0
    contents_removed: int = 0
    events_new: int = 0
    events_updated: int = 0
    events_removed: int = 0
    changes: list[Change] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: str | None = None

    @property
    def total_new(self) -> int:
        return self.courses_new + self.contents_new + self.events_new

    @property
    def total_updated(self) -> int:
        return self.courses_updated + self.contents_updated + self.events_updated

    @property
    def total_removed(self) -> int:
        return self.courses_removed + self.contents_removed + self.events_removed

    @property
    def has_changes(self) -> bool:
        return self.total_new > 0 or self.total_updated > 0

    @property
    def has_error(self) -> bool:
        return self.error is not None

    def summary(self) -> str:
        """خلاصه‌ی متنی."""
        if self.is_first_sync:
            return (
                f"🎉 اولین Sync: "
                f"{self.courses_new} درس، "
                f"{self.contents_new} فایل، "
                f"{self.events_new} رویداد"
            )

        if not self.has_changes:
            return "✨ هیچ تغییر جدیدی نیست"

        parts = []
        if self.courses_new:
            parts.append(f"{self.courses_new} درس جدید")
        if self.contents_new:
            parts.append(f"{self.contents_new} فایل جدید")
        if self.events_new:
            parts.append(f"{self.events_new} رویداد جدید")
        if self.total_updated:
            parts.append(f"{self.total_updated} به‌روزرسانی")

        return "📢 " + "، ".join(parts)

    def __repr__(self) -> str:
        return (
            f"SyncResult(first={self.is_first_sync}, "
            f"new={self.total_new}, "
            f"updated={self.total_updated}, "
            f"removed={self.total_removed})"
        )