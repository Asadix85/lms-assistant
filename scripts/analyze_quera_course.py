"""تحلیل HTML /course کوئرا."""

from pathlib import Path

from bs4 import BeautifulSoup


def main() -> None:
    html_path = Path("debug_quera_course.html")
    if not html_path.exists():
        print(f"❌ {html_path} پیدا نشد")
        return

    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    print("=" * 60)
    print("🔍 تحلیل صفحه‌ی /course کوئرا")
    print("=" * 60)

    # === ۱. پیدا کردن لینک‌های کلاس ===
    print("\n📎 لینک‌های /course/...:")
    course_links = soup.find_all("a", href=lambda h: h and h.startswith("/course/"))
    print(f"   تعداد: {len(course_links)}")

    # نشون دادن ۵ تای اول
    for i, link in enumerate(course_links[:5]):
        href = link.get("href", "")
        text = link.get_text(strip=True)[:60]
        print(f"\n  [{i+1}] href: {href}")
        print(f"      text: {text}")

        # کلاس‌های والد
        parent = link.parent
        for lvl in range(3):
            if parent is None:
                break
            classes = parent.get("class", [])
            if classes:
                print(f"      [{lvl}] parent class: {classes}")
            parent = parent.parent

    # === ۲. جستجوی الگوهای عنوان ===
    print("\n" + "=" * 60)
    print("🔍 جستجوی عنوان‌ها")
    print("=" * 60)

    # h1, h2, h3
    for tag_name in ["h1", "h2", "h3"]:
        tags = soup.find_all(tag_name)
        print(f"\n{tag_name}: {len(tags)} عدد")
        for t in tags[:3]:
            text = t.get_text(strip=True)[:80]
            classes = t.get("class", [])
            print(f"  - {text}  (class={classes})")

    # === ۳. پیدا کردن JSON داده‌ها ===
    print("\n" + "=" * 60)
    print("🔍 JSON data in page")
    print("=" * 60)

    # __NEXT_DATA__
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        text = next_data.string or ""
        print(f"\n__NEXT_DATA__: {len(text)} کاراکتر")
        print(f"  نمونه (اولین ۵۰۰): {text[:500]}")

    # script type=application/json
    json_scripts = soup.find_all("script", type="application/json")
    print(f"\n<script type=application/json>: {len(json_scripts)} عدد")
    for s in json_scripts[:3]:
        text = s.string or ""
        # فقط اگه داده مهم داره
        if len(text) > 100 and ("course" in text.lower() or "class" in text.lower()):
            print(f"\n  [{s.get('id', 'no-id')}] {len(text)} کاراکتر")
            print(f"  نمونه: {text[:300]}")


if __name__ == "__main__":
    main()