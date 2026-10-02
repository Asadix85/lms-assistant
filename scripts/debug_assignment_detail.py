"""Debug: ساختار دقیق assignment."""

from pathlib import Path

from bs4 import BeautifulSoup


# فایلی که ذخیره کردیم
path = Path("data/lms4.ui.ac.ir_assignment_sendreplay_38875.html")
html = path.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

print("=" * 70)
print(f"ساختار assignment/sendreplay/38875")
print("=" * 70)

# body id
body = soup.find("body")
print(f"body id: {body.get('id')}\n")

# === همه عناوین ===
print("عناوین (h1-h4):")
for h in soup.find_all(["h1", "h2", "h3", "h4"]):
    text = h.get_text(strip=True)
    if text and len(text) < 200:
        print(f"  [{h.name}] {text}")

# === فرم‌ها ===
print("\nفرم‌ها:")
for form in soup.find_all("form"):
    action = form.get("action", "")
    method = form.get("method", "get")
    print(f"  {method.upper()} {action}")
    for inp in form.find_all(["input", "textarea", "select"]):
        name = inp.get("name")
        itype = inp.get("type", inp.name)
        if name:
            print(f"    - {name} ({itype})")

# === دنبال کلمات کلیدی ===
print("\nکلمات کلیدی:")
for kw in ["مهلت", "تاریخ", "deadline", "due", "نمره", "پاسخ", "سوال", "عنوان"]:
    count = html.count(kw)
    if count > 0:
        print(f"  '{kw}': {count} بار")

# === متن اصلی ===
print("\nمتن اصلی صفحه (اول ۲۰۰۰ کاراکتر):")
main = soup.find(id="global_content")
if main:
    text = main.get_text(separator="\n", strip=True)
    print(text[:2000])