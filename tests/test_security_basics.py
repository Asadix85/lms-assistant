"""تست‌های پایه امنیت و پیام sync — بدون نیاز به LMS واقعی."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_password_hash_roundtrip():
    from src.web.security import hash_password, verify_password

    h = hash_password("Secret!123")
    assert verify_password("Secret!123", h)
    assert not verify_password("wrong", h)


def test_humanize_sync_error():
    from src.web.sync_messages import humanize_sync_error

    msg = humanize_sync_error("session expired 401")
    assert "LMS" in msg or "نشست" in msg
    assert humanize_sync_error(None)


def test_production_secret_required(monkeypatch=None):
    from src.web import security as sec

    # simulate production without key
    old = os.environ.get("LMS_ENV")
    old_key = os.environ.get("LMS_SECRET_KEY")
    try:
        os.environ["LMS_ENV"] = "production"
        os.environ.pop("LMS_SECRET_KEY", None)
        os.environ.pop("SECRET_KEY", None)
        try:
            sec.get_secret_key()
            assert False, "must raise"
        except RuntimeError:
            pass
    finally:
        if old is None:
            os.environ.pop("LMS_ENV", None)
        else:
            os.environ["LMS_ENV"] = old
        if old_key is not None:
            os.environ["LMS_SECRET_KEY"] = old_key
        else:
            os.environ.pop("LMS_SECRET_KEY", None)


def test_max_admins_constant():
    from src.web.security import MAX_ADMINS

    assert MAX_ADMINS == 3


if __name__ == "__main__":
    test_password_hash_roundtrip()
    test_humanize_sync_error()
    test_production_secret_required()
    test_max_admins_constant()
    print("OK")
