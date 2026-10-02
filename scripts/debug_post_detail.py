"""Debug: ساختار دقیق wall post."""

from pathlib import Path

from bs4 import BeautifulSoup


html = Path("data/wall_139710.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

print("=" * 70)
print("۱. ساختار feed_item_posted")
print("=" * 70)

posted_items = soup.find_all(class_="feed_item_posted")
for i, item in enumerate(posted_items, 1):
    print(f"\n--- Post {i} ---")
    print(f"HTML (اول ۱۰۰۰ کاراکتر):")
    print(str(item)[:1000])
    print()

# دنبال feed_item_body
print("\n" + "=" * 70)
print("۲. ساختار feed_item_body")
print("=" * 70)

body_items = soup.find_all(class_="feed_item_body")
for i, item in enumerate(body_items[:3], 1):
    print(f"\n--- Body {i} ---")
    print(f"HTML (اول ۱۵۰۰ کاراکتر):")
    print(str(item)[:1500])
    print()