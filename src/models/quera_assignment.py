"""مدل Quera Assignment (تمرین)."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QueraProblem:
    """یه سؤال توی یه تمرین."""

    id: str
    name: str
    type: str = "U"
    submission_score: float | None = None
    state: str = "NO_SUBMIT"

    @property
    def is_submitted(self) -> bool:
        return self.state != "NO_SUBMIT"


@dataclass
class QueraAssignment:
    """یه تمرین Quera."""

    id: str
    name: str
    course_name: str
    finish_time: datetime | None = None
    problems: list[QueraProblem] = field(default_factory=list)

    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    @property
    def problems_count(self) -> int:
        return len(self.problems)

    @property
    def submitted_count(self) -> int:
        return sum(1 for p in self.problems if p.is_submitted)

    @property
    def is_expired(self) -> bool:
        if not self.finish_time:
            return False
        now = self._now_aware()
        return now > self.finish_time

    @property
    def days_left(self) -> int:
        """روزهای مانده. منفی اگه گذشته."""
        if not self.finish_time:
            return -1
        now = self._now_aware()
        delta = self.finish_time - now
        return delta.days

    @property
    def time_left_text(self) -> str:
        """متن زمان مانده (مثلاً '۲ روز و ۵ ساعت')."""
        if not self.finish_time:
            return "بدون مهلت"

        now = self._now_aware()
        delta = self.finish_time - now

        if delta.total_seconds() < 0:
            return "گذشته"

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            return f"{days} روز و {hours} ساعت"
        elif hours > 0:
            return f"{hours} ساعت و {minutes} دقیقه"
        else:
            return f"{minutes} دقیقه"

    def _now_aware(self) -> datetime:
        """گرفتن now با timezone (برای مقایسه با finish_time)."""
        if self.finish_time and self.finish_time.tzinfo is not None:
            # اگه finish_time aware بود، now رو هم aware کن
            return datetime.now(timezone.utc)
        return datetime.now()

    def __repr__(self) -> str:
        return (
            f"QueraAssignment(id={self.id!r}, "
            f"name={self.name[:30]!r}, "
            f"problems={self.problems_count})"
        )