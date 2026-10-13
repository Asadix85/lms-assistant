"""مدل CourseSchedule (زمان + مکان کلاس)."""

from dataclasses import dataclass


@dataclass
class CourseSchedule:
    """اطلاعات زمان + مکان کلاس."""

    course_id: str
    weekday: str | None = None       # سه‌شنبه
    start_time: str | None = None    # 14:00
    end_time: str | None = None      # 16:00
    building: str | None = None      # ساختمان انصاری
    floor: str | None = None         # همکف
    room: str | None = None          # 135
    raw_text: str = ""

    @property
    def location(self) -> str:
        """مکان به صورت یک خط."""
        parts = []
        if self.building:
            parts.append(self.building)
        if self.floor:
            parts.append(f"طبقه {self.floor}")
        if self.room:
            parts.append(f"اتاق {self.room}")
        return " — ".join(parts)

    @property
    def time_range(self) -> str:
        """بازه‌ی زمانی."""
        if self.start_time and self.end_time:
            return f"{self.start_time} - {self.end_time}"
        return self.start_time or ""

    def __repr__(self) -> str:
        return (
            f"CourseSchedule(course={self.course_id!r}, "
            f"weekday={self.weekday!r}, time={self.time_range!r})"
        )