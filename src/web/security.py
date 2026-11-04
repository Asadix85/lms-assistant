"""امنیت وب: session token، هش، و رمزنگاری اسرار کاربر.

SECRET_KEY باید از محیط خوانده شود. در production حتماً یک مقدار
تصادفی بلند بگذار؛ در غیر این صورت اسرار قابل رمزگشایی می‌شوند.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

SESSION_COOKIE_NAME = "lms_session"
SESSION_DAYS = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return _utcnow().strftime("%Y-%m-%d %H:%M:%S")


def expires_in_days(days: int = SESSION_DAYS) -> str:
    return (_utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def parse_iso(value: str) -> datetime:
    # SQLite معمولاً بدون timezone ذخیره می‌کند؛ UTC فرض می‌کنیم.
    dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


def get_secret_key() -> str:
    key = os.environ.get("LMS_SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not key:
        # توسعه محلی — در production باید ست شود
        key = "dev-only-change-me-in-production-please-32b"
        logger.warning(
            "SECRET_KEY تنظیم نشده؛ از کلید توسعه استفاده می‌شود. "
            "قبل از deploy عمومی LMS_SECRET_KEY را ست کنید."
        )
    return key


def _fernet() -> Fernet:
    """کلید Fernet پایدار از SECRET_KEY مشتق می‌شود."""
    digest = hashlib.sha256(get_secret_key().encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plain: str) -> str:
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("رمزگشایی اسرار ناموفق بود (SECRET_KEY عوض شده؟)") from e


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """هش یک‌طرفه توکن session برای ذخیره در DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def hash_password(password: str) -> str:
    """هش پسورد محلی (PBKDF2-SHA256) — برای ادمین سایت، نه پسورد LMS."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


MAX_ADMINS = 3

