"""تست: login به هر سه دامنه به صورت جداگانه."""

import os
from dotenv import load_dotenv

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient

load_dotenv()


DOMAINS = {
    "lms3": "https://lms3.ui.ac.ir",
    "lms4": "https://lms4.ui.ac.ir",
    "lms5": "https://lms5.ui.ac.ir",
}


def main():
    username = os.environ["LMS_USERNAME"]
    password = os.environ["LMS_PASSWORD"]

    for name, url in DOMAINS.items():
        print(f"\n{'='*60}")
        print(f"🔐 Login به {name} ({url})")
        print('='*60)

        with LMSHttpClient(base_url=url, timeout=15) as client:
            auth = LMSAuth(client)
            try:
                success = auth.login(username, password)
                if success:
                    print(f"✅ {name}: ورود موفق (User ID: {auth.user_id})")

                    # تست: آیا به درس‌ها دسترسی داریم؟
                    r = client.get("/pages/nodeclass")
                    print(f"   /pages/nodeclass → {r.status_code} ({len(r.text)} bytes)")

                    if r.status_code == 200:
                        # شمردن درس‌ها
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(r.text, "lxml")
                        courses = soup.find_all("div", class_="classwig")
                        print(f"   تعداد درس‌ها: {len(courses)}")
                else:
                    print(f"❌ {name}: ورود ناموفق")

            except Exception as e:
                print(f"❌ {name}: خطا - {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()