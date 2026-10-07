"""تحلیل دقیق ساختار HTML کلاس‌های Quera."""

from pathlib import Path
from bs4 import BeautifulSoup


def main() -> None:
    html = Path("debug_quera_course.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    # پیدا کردن لینک‌های /course/{id}
    import re
    course_links = [
        a for a in soup.find_all("a", href=True)
        if re.match(r"^/course/\d+$", a["href"])
    ]

    print(f"📎 {len(course_links)} لینک کلاس\n")

    for i, link in enumerate(course_links[:2]):  # فقط ۲ تای اول
        print("=" * 60)
        print(f"📍 لینک #{i + 1}: {link.get('href')}")
        print("=" * 60)

        # HTML خام
        print("\n🔍 HTML خام:")
        print(link.prettify()[:1500])

        # متن
        print("\n📝 متن (separator='|'):")
        print(repr(link.get_text(separator="|", strip=True)))

        # divها
        divs = link.find_all("div")
        print(f"\n📦 {len(divs)} div:")
        for j, d in enumerate(divs):
            classes = d.get("class", [])
            text = d.get_text(strip=True)
            print(f"  [{j}] class={classes}")
            print(f"      text={text!r}")
            print(f"      string={repr(d.string)}")

        # spanها
        spans = link.find_all("span")
        print(f"\n📦 {len(spans)} span:")
        for j, s in enumerate(spans):
            print(f"  [{j}] {s.get_text(strip=True)!r}")

        print()


if __name__ == "__main__":
    main()