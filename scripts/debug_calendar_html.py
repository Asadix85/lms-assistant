"""Debug: دیدن ساختار HTML تقویم."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def main():
    Path("data").mkdir(exist_ok=True)

    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        assert assistant.login()

        r = assistant.client.get("https://lms4.ui.ac.ir/pages/calendar")
        html = r.text

        # ذخیره برای مرور
        Path("data/calendar_full.html").write_text(html, encoding="utf-8")
        print(f"ذخیره: data/calendar_full.html ({len(html)} bytes)\n")

        soup = BeautifulSoup(html, "lxml")

        # پیدا کردن اولین لینک joinfast
        first_link = None
        for a in soup.find_all("a", href=True):
            if "joinfast" in a["href"]:
                first_link = a
                break

        if not first_link:
            print("❌ هیچ لینک joinfast پیدا نشد")
            return

        print("=" * 70)
        print("ساختار HTML اطراف اولین لینک joinfast:")
        print("=" * 70)

        # نمایش ۵ سطح بالا
        current = first_link
        for level in range(6):
            if current is None:
                break
            print(f"\n{'  ' * level}=== سطح {level}: <{current.name}> ===")
            if current.name:
                attrs = " ".join(f'{k}="{v}"' for k, v in (current.attrs or {}).items())
                if attrs:
                    print(f"{'  ' * level}attrs: {attrs[:200]}")
                print(f"{'  ' * level}text: {current.get_text(separator=' ', strip=True)[:300]}")
            current = current.parent

        print("\n\n" + "=" * 70)
        print("HTML خام اطراف لینک (شامل ۱۵۰۰ کاراکتر قبل و بعد):")
        print("=" * 70)

        # پیدا کردن موقعیت لینک در HTML خام
        idx = html.find("joinfast")
        if idx > 0:
            start = max(0, idx - 500)
            end = min(len(html), idx + 1500)
            print(html[start:end])
        else:
            print("❌ joinfast در HTML پیدا نشد")


if __name__ == "__main__":
    main()