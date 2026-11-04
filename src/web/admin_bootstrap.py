"""ساخت ادمین محلی با یوزرنیم/رمز تصادفی.

فایل credentials در ریشهٔ پروژه نوشته می‌شود:
  <project_root>/admin_credentials.txt
مثال: F:\\Projects\\lms-assistant\\admin_credentials.txt
"""

from __future__ import annotations

import secrets
import string
from pathlib import Path

from loguru import logger

from src.storage.database import Database
from src.storage.repositories.user_repo import UserRepository
from src.web.security import MAX_ADMINS, hash_password

# src/web/admin_bootstrap.py → parents: web, src, project_root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "admin_credentials.txt"


def _random_username() -> str:
    return "admin_" + secrets.token_hex(3)


def _random_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _count_local_admins(repo: UserRepository) -> int:
    row = repo.db.fetch_one(
        """
        SELECT COUNT(*) AS n FROM users
         WHERE role = 'admin' AND COALESCE(auth_provider, 'lms') = 'local'
        """
    )
    return int(row["n"]) if row else 0


def ensure_local_admin(db: Database) -> None:
    """اگر ادمین محلی وجود ندارد و سقف ادمین پر نشده، یکی بساز."""
    repo = UserRepository(db)

    local_admins = _count_local_admins(repo)
    if local_admins > 0:
        logger.info(
            "ادمین محلی از قبل وجود دارد — فایل credentials بازنویسی نمی‌شود. مسیر مورد انتظار: {}",
            CREDENTIALS_FILE,
        )
        return

    total_admins = repo.count_admins()
    if total_admins >= MAX_ADMINS:
        logger.warning(
            "سقف ادمین ({}) پر است و ادمین محلی ساخته نشد. "
            "یکی از ادمین‌ها را به user تغییر بده یا از دیتابیس پاک کن.",
            MAX_ADMINS,
        )
        return

    username = _random_username()
    password = _random_password()
    password_hash = hash_password(password)

    try:
        user = repo.create_local_admin(
            username=username,
            password_hash=password_hash,
            full_name="مدیر سیستم",
        )
    except Exception as e:
        logger.error("ساخت ادمین محلی ناموفق: {}", e)
        raise

    lines = [
        "# LMS Assistant — مشخصات ورود ادمین محلی",
        "# این فایل را محرمانه نگه دارید و در git قرار ندهید.",
        f"username={username}",
        f"password={password}",
        f"user_id={user['id']}",
        "",
        "ورود از UI: دکمه «ورود ادمین (محلی)» در مودال لاگین",
        "یا POST /api/auth/local-login",
        f"سقف ادمین: {MAX_ADMINS}",
        f"path={CREDENTIALS_FILE}",
    ]
    try:
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CREDENTIALS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.warning("=== ادمین محلی ساخته شد ===")
        logger.warning("username: {}", username)
        logger.warning("password: {}", password)
        logger.warning("فایل: {}", CREDENTIALS_FILE.resolve())
    except Exception as e:
        # حتی اگر فایل نوشته نشود، در لاگ چاپ می‌شود
        logger.error(
            "نوشتن admin_credentials.txt ناموفق ({}). "
            "یوزرنیم={} رمز={} — همین را ذخیره کن.",
            e,
            username,
            password,
        )
