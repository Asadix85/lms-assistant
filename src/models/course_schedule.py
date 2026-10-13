"""مدل CourseSchedule (زمان + مکان کلاس)."""

from dataclasses import dataclass, field


@dataclass
class ClassSession:
    """یه جلسه‌ی کلاس (روز + ساعت + مکان)."""

    weekday: str = ""       # دوشنبه
    start_time: str = ""    # 09:00
    end_time: str = ""      # 10:00
    location: str = ""      # فني و مهندسي كلاس 25- مجتمع كلاسها طبقه دوم

    @property
    def time_range(self) -> str:
        if self.start_time and self.end_time:
            return f"{self.start_time}-{self.end_time}"
        return self.start_time or ""

    def to_text(self) -> str:
        """متن خوانا."""
        parts = []
        if self.weekday:
            parts.append(self.weekday)
        if self.time_range:
            parts.append(self.time_range)
        if self.location:
            parts.append(f"در {self.location}")
        return " ".join(parts)


@dataclass
class CourseSchedule:
    """برنامه‌ی یه درس."""

    course_id: str
    course_code: str = ""       # 36-20-313
    sessions: list[ClassSession] = field(default_factory=list)
    raw_text: str = ""

    @property
    def has_sessions(self) -> bool:
        return len(self.sessions) > 0

    def __repr__(self) -> str:
        return (
            f"CourseSchedule(course={self.course_id!r}, "
            f"sessions={len(self.sessions)})"
        )