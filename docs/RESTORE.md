بازیابی بکاپ دیتابیس

بکاپ‌های خودکار در کنار فایل دیتابیس، داخل پوشه backups/ ذخیره می‌شوند (نام‌هایی مثل lms_auto_YYYYMMDD_HHMMSS.db یا بکاپ دستی lms_*.db).

مراحل restore





سرور وب را متوقف کنید (Ctrl+C یا stop سرویس).



از فایل DB فعلی یک کپی اضطراری بگیرید.



فایل بکاپ را روی مسیر DB اصلی کپی/جایگزین کنید
(مسیر در config.settings / متغیر محیطی مربوط به db_path).



سرور را دوباره اجرا کنید.



با حساب ادمین وارد شوید و یک همگام‌سازی آزمایشی بزنید.

متغیرهای محیطی مرتبط





LMS_BACKUP_INTERVAL_HOURS (پیش‌فرض ۲۴)



LMS_BACKUP_KEEP تعداد فایل‌های نگه‌داشته‌شده (پیش‌فرض ۱۴)



LMS_ENV=production



LMS_SECRET_KEY (اجباری در production)



LMS_COOKIE_SECURE=1 روی HTTPS

