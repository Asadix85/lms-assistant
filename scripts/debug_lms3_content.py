"""Debug: کشف endpoint محتوای lms3."""

import os
from pathlib import Path

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.services.lms_assistant import LMSAssistant

load_dotenv()


def main():
    with LMSAssistant(
        username=os.environ["LMS_USERNAME"],
        password=os.environ["LMS_PASSWORD"],
    ) as assistant:
        # ۱. Login
        assert assistant.login()

        # ۲. دریافت درس‌ها
        courses = assistant.get_all_courses()

        # ۳. پیدا کردن یک درس lms3
        lms3_course = None
        for c in courses:
            if c.domain == "lms3" and c.is_active:
                lms3_course = c
                break

        if not lms3_course:
            print("❌ درس lms3 پیدا نشد")
            return

        print(f"📚 درس انتخاب شده: {lms3_course.name}")
        print(f"   domain: {lms3_course.domain}")
        print(f"   group_id: {lms3_course.group_id}")
        print(f"   nodeg_url: {lms3_course.nodeg_url[:60]}..." if lms3_course.nodeg_url else "   nodeg_url: None")
        print()

        # ۴. تست endpointهای احتمالی
        candidates = [
            f"https://lms3.ui.ac.ir/group/index/listofcontent/?group_id={lms3_course.group_id}",
            f"https://lms3.ui.ac.ir/nodeg/{lms3_course.group_id}/listofcontent",
            lms3_course.url.replace("/2", "/listofcontent") if lms3_course.nodeg_url else None,
            lms3_course.url.replace("/2", "/files") if lms3_course.nodeg_url else None,
            lms3_course.url,  # خود صفحه درس
        ]

        print("🧪 تست endpointها:")
        for url in candidates:
            if not url:
                continue
            try:
                r = assistant.client.get(url, timeout=30)
                print(f"  {url[:80]}")
                print(f"    → {r.status_code} ({len(r.text)} bytes)")

                # اگر 200 بود، ذخیره کن
                if r.status_code == 200 and len(r.text) > 5000:
                    soup = BeautifulSoup(r.text, "lxml")
                    body = soup.find("body")
                    body_id = body.get("id") if body else "?"
                    print(f"    body id: {body_id}")

                    # چک فایل‌ها
                    pdf_count = r.text.lower().count(".pdf")
                    zip_count = r.text.lower().count(".zip")
                    public_count = r.text.lower().count("/public/")
                    print(f"    .pdf: {pdf_count}, .zip: {zip_count}, /public/: {public_count}")

                    # ذخیره
                    fname = url.split("/")[-1].split("?")[0] or "index"
                    path = Path(f"data/lms3_{fname}_{lms3_course.group_id}.html")
                    path.write_text(r.text, encoding="utf-8")
                    print(f"    ذخیره: {path}")
                print()
            except Exception as e:
                print(f"  {url[:80]}")
                print(f"    → خطا: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()