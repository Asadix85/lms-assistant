"""تست پارسر برنامه‌ی هفتگی."""

from pathlib import Path

from src.parsers.course_schedule_parser import CourseScheduleParser


def main() -> None:
    html_path = Path("debug_wall.html")
    if not html_path.exists():
        print(f"❌ {html_path} پیدا نشد")
        return

    html = html_path.read_text(encoding="utf-8")

    parser = CourseScheduleParser()
    schedule = parser.parse(html, course_id="139710")

    if not schedule:
        print("❌ پارسر چیزی پیدا نکرد")
        return

    print("=" * 60)
    print(f"🎯 درس: {schedule.course_id}")
    print(f"📋 کد درس: {schedule.course_code}")
    print(f"📊 تعداد جلسات: {len(schedule.sessions)}")
    print("=" * 60)

    for i, s in enumerate(schedule.sessions):
        print(f"\n[{i + 1}] {s.weekday}")
        print(f"    ⏰ {s.time_range}")
        print(f"    📍 {s.location}")


if __name__ == "__main__":
    main()