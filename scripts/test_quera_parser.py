"""تست parser کوئرا."""

from pathlib import Path

from src.parsers.quera import QueraParser


def main() -> None:
    html_path = Path("debug_quera_course.html")
    if not html_path.exists():
        print(f"❌ {html_path} پیدا نشد")
        return

    html = html_path.read_text(encoding="utf-8")

    parser = QueraParser()
    assignments = parser.parse_course_page(html)

    print("=" * 60)
    print(f"🎯 {len(assignments)} تمرین پیدا شد")
    print("=" * 60)

    for i, a in enumerate(assignments):
        print(f"\n[{i+1}] {a.name}")
        print(f"    🆔 {a.id}")
        print(f"    📚 {a.course_name}")
        print(f"    ⏰ ددلاین: {a.finish_time}")
        print(f"    📅 {a.days_left} روز مانده" if a.days_left >= 0 else "    ⚠️ گذشت")
        print(f"    📋 {a.submitted_count}/{a.problems_count} سؤال انجام‌شده")

        for p in a.problems[:3]:  # فقط ۳ تای اول
            status = "✅" if p.is_submitted else "⏳"
            print(f"        {status} {p.name} ({p.id})")
        if len(a.problems) > 3:
            print(f"        ... و {len(a.problems) - 3} سؤال دیگر")


if __name__ == "__main__":
    main()