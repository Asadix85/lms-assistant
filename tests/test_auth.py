"""تست LMSAuth."""

import os
from pathlib import Path

from dotenv import load_dotenv

from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient


# خواندن .env
load_dotenv()


def test_login_success():
    """تست ورود موفق با اعتبارنامه واقعی."""
    username = os.environ["LMS_USERNAME"]
    password = os.environ["LMS_PASSWORD"]

    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        auth = LMSAuth(client)

        # قبل از ورود
        assert not auth.is_authenticated
        assert auth.user_id is None

        # ورود
        result = auth.login(username, password)

        # بررسی
        assert result is True, "ورود باید موفق باشد"
        assert auth.is_authenticated
        assert auth.user_id is not None
        print(f"✅ ورود موفق. User ID: {auth.user_id}")

        # تست verify
        assert auth.verify(), "session باید معتبر باشد"
        print("✅ verify موفق")


def test_login_failure():
    """تست ورود ناموفق با رمز اشتباه."""
    with LMSHttpClient(base_url="https://lms4.ui.ac.ir") as client:
        auth = LMSAuth(client)

        result = auth.login("wrong_user", "wrong_pass")

        assert result is False, "ورود باید ناموفق باشد"
        assert not auth.is_authenticated
        print("✅ ورود ناموفق درست تشخیص داده شد")


if __name__ == "__main__":
    print("تست ۱: ورود موفق")
    test_login_success()

    print("\nتست ۲: ورود ناموفق")
    test_login_failure()

    print("\n🎉 همه تست‌ها موفق!")