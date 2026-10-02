"""تست استخراج نام تکلیف از HTML."""

from pathlib import Path

from bs4 import BeautifulSoup


html = Path("data/wall_139710.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

# پیدا کردن همه feed_item_body
for i, body in enumerate(soup.find_all("div", class_="feed_item_body"), 1):
    attachments = body.find("div", class_="feed_item_attachments")
    if not attachments:
        continue

    # دنبال span با "عنوان"
    print(f"=== Feed Body {i} ===")
    for span in attachments.find_all("span"):
        text = span.get_text(strip=True)
        if "عنوان" in text:
            print(f"متن span: {text}")
            print(f"طول: {len(text)} کاراکتر")

            b = span.find("b")
            if b:
                b_text = b.get_text(strip=True)
                print(f"متن b: {b_text}")
                print(f"طول b: {len(b_text)} کاراکتر")
                print(f"HTML b: {str(b)[:500]}")
            print()