"""تست: دسترسی به درس lms3 از طریق توکن nodeg."""

import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


def main():
    # ۱. Login به lms4
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir", timeout=30) as client:
        auth = LMSAuth(client)
        if not auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"]):
            print("❌ Login to lms4 failed")
            return

        print(f"✅ Logged in to lms4. User ID: {auth.user_id}\n")

        # ۲. دریافت لیست درس‌ها
        r = client.get("/pages/nodeclass")
        soup = BeautifulSoup(r.text, "lxml")

        # ۳. پیدا کردن اولین لینک lms3
        lms3_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "lms3.ui.ac.ir/nodeg/" in href:
                lms3_url = href
                break

        if not lms3_url:
            print("❌ لینک lms3 پیدا نشد")
            return

        print(f"🔗 اولین لینک lms3 (redacted):")
        # redact: فقط دامنه و ساختار
        parts = lms3_url.split("/")
        print(f"   https://{parts[2]}/nodeg/<TOKEN>/{parts[4]}/{parts[5]}\n")

        # ۴. تلاش برای دسترسی به این URL از داخل همین client
        print(f"🧪 تست: GET {lms3_url[:50]}...")
        try:
            r = client.get(lms3_url, timeout=30)
            print(f"Status: {r.status_code}")
            print(f"URL نهایی: {r.url}")
            print(f"طول HTML: {len(r.text)}")

            # چک: آیا لاگین شدیم؟
            soup3 = BeautifulSoup(r.text, "lxml")
            body = soup3.find("body")
            print(f"body id: {body.get('id') if body else 'N/A'}")

            if "user_form_login" in r.text:
                print("❌ فرم لاگین در صفحه (یعنی هنوز لاگین نیستیم)")
            else:
                print("✅ به نظر می‌رسد وارد lms3 شده‌ایم!")

                # ذخیره برای بررسی
                Path = __import__("pathlib").Path
                Path("data").mkdir(exist_ok=True)
                Path("data/lms3_course_via_nodeg.html").write_text(r.text, encoding="utf-8")
                print("   ذخیره شد: data/lms3_course_via_nodeg.html")

                # دنبال فایل‌های محتوا بگرد
                print("\n📁 لینک‌های محتوا در lms3:")
                count = 0
                for a in soup3.find_all("a", href=True):
                    href = a["href"]
                    if any(x in href.lower() for x in [".pdf", ".zip", ".docx", "/public/", "listofcontent", "pluginfile"]):
                        print(f"   {href[:100]}")
                        count += 1
                        if count >= 10:
                            break
                if count == 0:
                    print("   هیچ فایلی پیدا نشد")

        except Exception as e:
            print(f"❌ خطا: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()