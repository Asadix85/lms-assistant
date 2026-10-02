"""تست WallParser."""

from pathlib import Path

from src.parsers.wall import WallParser


def test_wall_parser():
    html = Path("data/wall_139710.html").read_text(encoding="utf-8")
    parser = WallParser(course_id="139710")
    posts, assignments = parser.parse(html)

    print(f"\n📝 {len(posts)} پست:")
    for p in posts:
        print(f"  • {p.author}: {p.text[:60]}")
        print(f"    تاریخ: {p.posted_at} ({p.posted_at_jalali})")

    print(f"\n📋 {len(assignments)} تکلیف:")
    for a in assignments:
        print(f"  • {a.title[:60]}")
        print(f"    شروع: {a.start_at}")
        print(f"    ددلاین: {a.deadline} ({a.deadline_jalali})")
        print(f"    پاسخ‌ها: {a.response_count}")


if __name__ == "__main__":
    test_wall_parser()