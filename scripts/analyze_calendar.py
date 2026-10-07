"""تحلیل HTML تقویم LMS برای فهمیدن ساختار تاریخ."""

from pathlib import Path
from bs4 import BeautifulSoup


def main() -> None:
    html_path = Path("debug_calendar.html")
    if not html_path.exists():
        print(f"❌ فایل پیدا نشد: {html_path}")
        return

    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    print("=" * 60)
    print("🔍 تحلیل HTML تقویم")
    print("=" * 60)

    # === ۱. پیدا کردن لینک‌های joinfast ===
    joinfast_links = soup.find_all("a", href=lambda h: h and "joinfast" in h)
    print(f"\n📎 تعداد joinfast link: {len(joinfast_links)}")

    if not joinfast_links:
        print("❌ هیچ joinfast link پیدا نشد!")
        return

    # === ۲. تحلیل اولین ۳ تا ===
    print("\n" + "=" * 60)
    print("🔬 تحلیل ۳ لینک اول")
    print("=" * 60)

    for i, link in enumerate(joinfast_links[:3]):
        print(f"\n{'─' * 60}")
        print(f"📍 لینک #{i + 1}")
        print(f"{'─' * 60}")

        # URL
        href = link.get("href", "")
        print(f"URL: {href[:80]}...")

        # === والدها ===
        print("\n🌳 والدها (خانواده):")
        parent = link.parent
        for level in range(6):
            if parent is None:
                break

            attrs = dict(parent.attrs) if parent.attrs else {}
            # فیلتر کردن attrs
            attrs_str = ", ".join(f"{k}={v!r}" for k, v in attrs.items())
            if len(attrs_str) > 100:
                attrs_str = attrs_str[:100] + "..."

            print(f"  [{level}] <{parent.name}> {attrs_str}")

            # اگه data-date داره، نشون بده
            for key in parent.attrs:
                if any(x in key.lower() for x in ["date", "day", "jalali", "shamsi", "time"]):
                    print(f"      🔑 {key} = {parent.attrs[key]!r}")

            parent = parent.parent

        # === متن والدها ===
        print("\n📝 متن والد (۲ سطح بالا):")
        ancestor = link.parent
        for _ in range(2):
            if ancestor and ancestor.parent:
                ancestor = ancestor.parent

        if ancestor:
            text = ancestor.get_text(separator=" ", strip=True)
            if len(text) > 200:
                text = text[:200] + "..."
            print(f"  {text}")

        # === متن داخل link ===
        print("\n📝 متن داخل link:")
        inner_text = link.get_text(separator=" ", strip=True)
        if len(inner_text) > 200:
            inner_text = inner_text[:200] + "..."
        print(f"  {inner_text}")

    # === ۳. جستجوی الگوهای تاریخ ===
    print("\n" + "=" * 60)
    print("🔍 جستجوی الگوهای تاریخ")
    print("=" * 60)

    html_str = str(soup)

    import re

    # شمسی (۱۴۰۵-۰۷-۱۵ یا 1405/07/15)
    patterns = {
        "شمسی (YYYY-MM-DD)": r"1[34]\d{2}[-/]\d{1,2}[-/]\d{1,2}",
        "میلادی (YYYY-MM-DD)": r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}",
        "data-date": r'data-date="([^"]+)"',
        "data-jalali": r'data-jalali="([^"]+)"',
        "data-day": r'data-day="([^"]+)"',
    }

    for name, pattern in patterns.items():
        matches = re.findall(pattern, html_str)
        if matches:
            unique = list(set(matches))[:5]
            print(f"\n✅ {name}: {len(matches)} مورد")
            print(f"   نمونه: {unique}")
        else:
            print(f"\n❌ {name}: پیدا نشد")


if __name__ == "__main__":
    main()