"""وضعیت پیشرفت Sync برای نمایش در UI."""

from collections.abc import Callable
from dataclasses import dataclass, field


# وزن هر فاز برای محاسبه‌ی درصد کل
# (مجموع = 1.0)
PHASE_WEIGHTS: dict[str, float] = {
    "login": 0.08,
    "courses": 0.10,
    "schedules": 0.07,
    "contents": 0.22,
    "events": 0.05,
    "wall": 0.28,
    "members": 0.20,
}


@dataclass
class SyncProgress:
    """وضعیت لحظه‌ای Sync."""

    # === فاز ===
    phase: str = "idle"
    """نام فاز فعلی: idle, login, courses, contents, events, wall, members."""

    phase_index: int = 0
    """شماره‌ی فاز (0-based)."""

    total_phases: int = 6
    """تعداد کل فازها."""

    # === آیتم ===
    current: int = 0
    """آیتم فعلی در فاز."""

    total: int = 0
    """کل آیتم‌های فاز."""

    # === متن ===
    message: str = ""
    """پیام وضعیت (مثلاً 'در حال دریافت محتوا...')."""

    # === تغییرات زنده ===
    changes: dict[str, int] = field(default_factory=dict)
    """تغییرات زنده: {'posts': 2, 'assignments': 1, ...}"""

    # === زمان ===
    elapsed: float = 0.0
    """زمان سپری‌شده (ثانیه)."""

    # === محاسبات ===

    @property
    def percent(self) -> int:
        """درصد کل (0-100) با وزن‌دهی فازها."""
        if self.phase == "idle":
            return 0
        if self.phase == "done":
            return 100

        # بخش تمام‌شده = مجموع وزن فازهای قبلی
        completed_weight = 0.0
        for i, (name, weight) in enumerate(PHASE_WEIGHTS.items()):
            if i < self.phase_index:
                completed_weight += weight

        # بخش فعلی = وزن فاز فعلی × نسبت پیشرفت درون فاز
        current_weight = PHASE_WEIGHTS.get(self.phase, 0.0)
        if self.total > 0:
            in_phase_ratio = min(self.current / self.total, 1.0)
        else:
            in_phase_ratio = 0.0

        total = completed_weight + (current_weight * in_phase_ratio)
        return int(total * 100)

    @property
    def elapsed_text(self) -> str:
        """زمان سپری‌شده به صورت متن فارسی."""
        if self.elapsed < 60:
            return f"{self.elapsed:.0f} ثانیه"
        minutes = int(self.elapsed // 60)
        seconds = int(self.elapsed % 60)
        return f"{minutes}:{seconds:02d} دقیقه"

    @property
    def changes_text(self) -> str:
        """تغییرات زنده به صورت متن."""
        if not self.changes:
            return ""

        labels = {
            "courses": "درس",
            "contents": "فایل",
            "events": "رویداد",
            "posts": "پست",
            "assignments": "تکلیف",
            "members": "عضو",
        }

        parts = []
        for key, count in self.changes.items():
            if count > 0:
                label = labels.get(key, key)
                parts.append(f"{count} {label}")

        if not parts:
            return ""

        return "📢 " + "، ".join(parts) + " جدید"


# Type alias برای callback
ProgressCallback = Callable[[SyncProgress], None]