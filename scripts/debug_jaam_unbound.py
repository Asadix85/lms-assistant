"""Debug: بررسی jaam/unbound/index (لیست جلسات آزاد/آزمون‌ها)."""

from pathlib import Path
from bs4 import BeautifulSoup


def main():
    path = Path("data/jaam_unbound_lms4.html")
    if not path.exists():
        print(f"❌ فایل پیدا نشد: {path}")
        return

    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    print(f"طول HTML: {len(html)} کاراکتر")
    body = soup.find("body")
    print(f"body id: {body.get('id')}\n")

    # === ۱. همه لینک‌ها ===
    print("=== همه لینک‌های داخلی ===")
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href in seen or href.startswith("#"):
            continue
        seen.add(href)
        text = a.get_text(strip=True)[:60]
        print(f"  {href} → {text}")

    # === ۲. جدول‌ها ===
    print("\n=== جدول‌ها ===")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        print(f"  جدول با {len(rows)} سطر")
        if rows:
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
            print(f"    ستون‌ها: {headers}")
            # نمونه سطر دوم
            if len(rows) > 1:
                cells = [td.get_text(strip=True)[:30] for td in rows[1].find_all(["th", "td"])]
                print(f"    نمونه: {cells}")

    # === ۳. عناوین ===
    print("\n=== عناوین (h1-h4) ===")
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = h.get_text(strip=True)
        if text and len(text) < 100:
            print(f"  [{h.name}] {text}")

    # === ۴. divهای کلاس‌دار ===
    print("\n=== divهای کلاس‌دار (مهم) ===")
    seen_classes = set()
    for div in soup.find_all("div", class_=True):
        classes = tuple(div.get("class", []))
        if classes in seen_classes:
            continue
        seen_classes.add(classes)
        text = div.get_text(strip=True)[:60]
        if text and len(text) > 5:
            print(f"  [{' '.join(classes)}] {text}")

    # === ۵. جستجوی کلمات کلیدی ===
    print("\n=== کلمات کلیدی ===")
    keywords = ["آزمون", "امتحان", "کوییز", "quiz", "exam", "جلسه", "room",
                "زمان", "تاریخ", "مهلت", "شروع", "پایان", "joinfast", "jaam"]
    for kw in keywords:
        count = html.count(kw)
        if count > 0:
            print(f"  '{kw}': {count} بار")


if __name__ == "__main__":
    main()