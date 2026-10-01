"""تست: آیا session بین دامنه‌ها مشترک است؟"""

import os
from dotenv import load_dotenv

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


def main():
    # Login به lms4
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        auth = LMSAuth(client)
        if not auth.login(os.environ["LMS_USERNAME"], os.environ["LMS_PASSWORD"]):
            print("❌ Login failed")
            return

        print(f"✅ Logged in to lms4. User ID: {auth.user_id}")
        print(f"Cookies: {list(client.cookies.keys())}\n")

        # تست دامنه‌های دیگر
        for domain in ["lms3.ui.ac.ir", "lms5.ui.ac.ir"]:
            print(f"=== تست {domain} ===")
            try:
                r = client.get(f"https://{domain}/pages/nodemain")

                # چک: آیا در صفحه لاگین هستیم؟
                is_logged_in = (
                    "logout" in r.text.lower()
                    or "خروج" in r.text
                    or "nodemain" in str(r.url)
                )
                is_login_page = (
                    "user_form_login" in r.text
                    or "ورود" in r.text and "رمز عبور" in r.text
                )

                if is_logged_in and not is_login_page:
                    print(f"✅ در {domain} لاگین هستیم")
                    print(f"   URL نهایی: {r.url}")
                else:
                    print(f"❌ در {domain} لاگین نیستیم")
                    print(f"   URL نهایی: {r.url}")
            except Exception as e:
                print(f"❌ خطا: {e}")
            print()


if __name__ == "__main__":
    main()