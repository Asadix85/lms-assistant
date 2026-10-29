"""تست زنده ماندن نشست (Session) در LMS و Quera با پینگ دوره‌ای."""

import time
from datetime import datetime

from loguru import logger

from src.services.lms_assistant import LMSAssistant
from src.services.quera_sync import QueraSyncService
from src.core.quera_client import QueraHttpClient
from src.core.quera_auth import QueraAuth
from src.services.credential_provider import CredentialProvider

# تنظیمات تست
PING_INTERVAL_SECONDS = 60  # هر ۶۰ ثانیه پینگ کن
MAX_TEST_DURATION_MINUTES = 120  # تست را حداکثر ۲ ساعت ادامه بده


def test_lms_lifetime(creds):
    logger.info("🚀 شروع تست برای LMS...")
    assistant = LMSAssistant(creds.lms_username, creds.lms_password)
    
    if not assistant.login():
        logger.error("❌ لاگین اولیه به LMS ناموفق بود.")
        return

    logger.success("✅ لاگین اولیه موفق. شروع پینگ‌ها...")
    start_time = time.time()
    
    try:
        while True:
            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes > MAX_TEST_DURATION_MINUTES:
                logger.info("⏰ زمان تست به پایان رسید.")
                break

            # پینگ به یک صفحه که نیاز به احراز هویت دارد
            try:
                r = assistant.client.get("/pages/nodemain")
                # اگر سامانه ما را به صفحه لاگین ریدایرکت کند، یعنی نشست مرده است
                if "/login" in str(r.url) or "لاگین شما منقضی شده" in r.text:
                    logger.warning(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] نشست LMS منقضی شد! (بعد از {elapsed_minutes:.1f} دقیقه)")
                    # تلاش برای لاگین مجدد
                    logger.info("🔄 تلاش برای لاگین مجدد...")
                    if assistant.login():
                        logger.success("✅ لاگین مجدد موفق.")
                    else:
                        logger.error("❌ لاگین مجدد ناموفق.")
                        break
                else:
                    logger.debug(f"💚 [{datetime.now().strftime('%H:%M:%S')}] LMS زنده است (URL: {r.url})")
            except Exception as e:
                logger.error(f"خطا در پینگ LMS: {e}")

            time.sleep(PING_INTERVAL_SECONDS)
            
    finally:
        assistant.close()


def test_quera_lifetime(creds):
    logger.info("🚀 شروع تست برای Quera...")
    
    if not creds.quera_username or not creds.quera_password:
        logger.warning("اطلاعات کوئرا موجود نیست. تست کوئرا رد شد.")
        return

    client = QueraHttpClient()
    auth = QueraAuth(client)
    
    if not auth.login(creds.quera_username, creds.quera_password):
        logger.error("❌ لاگین اولیه به Quera ناموفق بود.")
        return

    logger.success("✅ لاگین اولیه به Quera موفق. شروع پینگ‌ها...")
    start_time = time.time()

    try:
        while True:
            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes > MAX_TEST_DURATION_MINUTES:
                logger.info("⏰ زمان تست به پایان رسید.")
                break

            try:
                # پینگ به داشبورد کوئرا
                r = client.get("/dashboard")
                # اگر ریدایرکت شد به صفحه لاگین، یعنی نشست مرده
                if "/accounts/login" in str(r.url):
                    logger.warning(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] نشست Quera منقضی شد! (بعد از {elapsed_minutes:.1f} دقیقه)")
                    logger.info("🔄 تلاش برای لاگین مجدد...")
                    if auth.login(creds.quera_username, creds.quera_password):
                        logger.success("✅ لاگین مجدد موفق.")
                    else:
                        logger.error("❌ لاگین مجدد ناموفق.")
                        break
                else:
                    logger.debug(f"💚 [{datetime.now().strftime('%H:%M:%S')}] Quera زنده است (URL: {r.url})")
            except Exception as e:
                logger.error(f"خطا در پینگ Quera: {e}")

            time.sleep(PING_INTERVAL_SECONDS)

    finally:
        client.close()


if __name__ == "__main__":
    logger.info("شروع تست طول عمر نشست...")
    creds = CredentialProvider.get()
    
    if not creds.lms_username:
        logger.error("اطلاعات LMS یافت نشد. لطفاً ابتدا در برنامه لاگین کنید یا .env را تنظیم کنید.")
    else:
        # برای اینکه تست سریع انجام شود، می‌توانید هر دو را همزمان تست کنید
        test_lms_lifetime(creds)
        # test_quera_lifetime(creds) 