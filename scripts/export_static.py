#!/usr/bin/env python
"""Sync LMS + ساخت سایت استاتیک برای GitHub Pages.

این اسکریپت در GitHub Actions اجرا می‌شود (و به‌صورت دستی روی سیستم محلی):

منابع اعتبارنامه (به ترتیب اولویت):
  1) متغیرهای محیطی: LMS_USERNAME / LMS_PASSWORD / QUERA_USERNAME / QUERA_PASSWORD
     (در Actions از GitHub Secrets پر می‌شوند — محل امن)
  2) Windows Credential Manager (keyring) برای اجرای دستی محلی

اگر هیچ اعتبارنامه‌ای موجود نبود یا لاگین/سینک ناموفق بود، از آخرین
data/lms.db موجود در ریپو خروجی می‌گیرد تا سایت همیشه محتوا داشته باشد.

رمزنگاری: اگر SITE_PASSPHRASE ست شده باشد، باندل داده با AES-256-GCM
رمزنگاری می‌شود و سایت در مرورگر (WebCrypto) با همان عبارت رمز باز می‌شود.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger

from src.services.credential_provider import CredentialProvider, Credentials
from src.services.lms_assistant import LMSAssistant
from src.services.quera_sync import QueraSyncService
from src.services.sync_service import SyncService
from src.storage.database import Database
from src.web.static_export import build_bundle, write_site

DB_PATH = Path("./data/lms.db")


def get_credentials() -> Credentials | None:
    """اعتبارنامه از env (Secrets) و سپس keyring محلی."""
    creds = Credentials(
        lms_username=os.environ.get("LMS_USERNAME", "").strip(),
        lms_password=os.environ.get("LMS_PASSWORD", ""),
        quera_username=os.environ.get("QUERA_USERNAME", "").strip(),
        quera_password=os.environ.get("QUERA_PASSWORD", ""),
    )
    if creds.lms_username and creds.lms_password:
        return creds

    try:
        local = CredentialProvider.load()
        if local.lms_username and local.lms_password:
            logger.info("استفاده از اعتبارنامه‌های ذخیره‌شده‌ی محلی (keyring)")
            return local
    except Exception as e:
        logger.warning(f"خواندن keyring ممکن نشد: {e}")
    return None


def run_live_sync(creds: Credentials) -> tuple[str, str | None]:
    """لاگین LMS + سینک کامل + (اختیاری) سینک کوئرا. خروجی: (source, full_name)."""
    assistant = LMSAssistant(creds.lms_username, creds.lms_password)
    if not assistant.login():
        raise RuntimeError("Login به LMS ناموفق بود")

    full_name = getattr(assistant, "full_name", None) or None
    db = Database(DB_PATH)
    result = SyncService(assistant, db).sync()
    logger.info(f"✅ سینک LMS: {result.summary()}")
    if result.has_error:
        logger.warning(f"سینک با خطا همراه بود: {result.error}")

    if creds.quera_username and creds.quera_password:
        try:
            q = QueraSyncService(creds.quera_username, creds.quera_password, db).sync()
            logger.info(f"✅ سینک Quera: {q}")
        except Exception as e:
            logger.warning(f"سینک Quera ممکن نشد: {e}")

    db.close()
    return "live", full_name


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="site", help="پوشه خروجی سایت (پیش‌فرض: site)")
    parser.add_argument("--passphrase", default=os.environ.get("SITE_PASSPHRASE", ""))
    parser.add_argument("--cname", default=os.environ.get("CNAME", ""))
    parser.add_argument("--skip-sync", action="store_true", help="بدون سینک، فقط اکسپورت از دیتابیس موجود")
    args = parser.parse_args()

    creds = get_credentials()
    source, full_name = "db", None

    if creds and not args.skip_sync:
        try:
            source, full_name = run_live_sync(creds)
        except Exception as e:
            logger.warning(
                f"سینک زنده ممکن نشد ({e}) — استفاده از آخرین دیتابیس موجود در ریپو"
            )

    if not DB_PATH.exists():
        logger.error(
            "دیتابیس data/lms.db موجود نیست؛ ابتدا یک‌بار sync محلی انجام دهید "
            "یا اعتبارنامه‌ها را در Secrets تنظیم کنید"
        )
        sys.exit(1)

    db = Database(DB_PATH)
    try:
        bundle = build_bundle(
            db,
            full_name=full_name,
            username=creds.lms_username if creds else None,
            source=source,
            generated_at=datetime.now().isoformat(timespec="seconds"),
        )
    finally:
        db.close()

    write_site(
        bundle,
        args.out,
        passphrase=args.passphrase or None,
        cname=args.cname or None,
    )


if __name__ == "__main__":
    main()
