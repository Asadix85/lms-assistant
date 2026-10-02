"""Debug: استخراج متن کامل wall posts."""

import re
from pathlib import Path

from bs4 import BeautifulSoup


html = Path("data/wall_139710.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

# پیدا کردن divهای wall
print("=" * 70)
print("Wall Posts (متن کامل)")
print("=" * 70)

# دنبال div با کلاس "feed_item_posted" یا مشابه
for cls in ["feed_item_posted", "feed_item_body", "wall-post", "feed"]:
    elements = soup.find_all(class_=lambda x: x and cls in str(x).lower())
    if elements:
        print(f"\nکلاس '{cls}': {len(elements)} مورد")
        for i, el in enumerate(elements[:3], 1):
            text = el.get_text(separator=" ", strip=True)[:200]
            print(f"  {i}. {text}")

# جستجوی مستقیم
print("\n" + "=" * 70)
print("جستجوی کلمات کلیدی در HTML")
print("=" * 70)

for kw in ["تمرین", "تکلیف", "مهلت", "تحویل", "پروژه", "جلسه", "فصل"]:
    if kw in html:
        print(f"\n'{kw}' پیدا شد:")
        idx = html.find(kw)
        # متن اطراف
        snippet = html[max(0, idx - 200):idx + 300]
        clean = BeautifulSoup(snippet, "lxml").get_text(separator=" ", strip=True)
        print(f"  ...{clean}...")