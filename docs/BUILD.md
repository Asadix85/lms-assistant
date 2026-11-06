ساخت EXE و Setup — LMS Assistant

نسخه فعلی از src/version.py خوانده می‌شود (APP_VERSION).

پیش‌نیاز





Python 3.11+ و .venv فعال



وابستگی‌های پروژه نصب باشد



(اختیاری) Inno Setup 6 برای فایل Setup

.\.venv\Scripts\Activate.ps1
pip install pyinstaller

۱) ساخت پوشه‌ی برنامه (onedir)

از ریشه‌ی پروژه:

.\scripts\build_exe.ps1
# یا تمیز:
.\scripts\build_exe.ps1 -Clean

خروجی:

dist\LMSAssistant\
  LMSAssistant.exe
  _internal\          ← DLLها و assets
  ...

برای تست دستی همان LMSAssistant.exe را اجرا کنید.
کل پوشه‌ی LMSAssistant باید با هم جابه‌جا شود (نه فقط exe).

۲) ساخت نصب‌کننده ویندوز





Inno Setup را نصب کنید



فایل packaging\installer.iss را باز کنید



Build → Compile

خروجی:

dist\installer\LMSAssistant-Setup-0.2.0.exe

ساختار مرتبط







مسیر



نقش





src/version.py



نسخه و نام برنامه (منبع واحد)





packaging/lms_assistant.spec



تنظیمات PyInstaller





packaging/version_info.txt



متادیتای فایل ویندوز





packaging/installer.iss



اسکریپت Inno Setup





scripts/build_exe.ps1



اسکریپت یک‌کلیکی build

نکات مهندسی





onedir انتخاب شد نه onefile: استارتاپ سریع‌تر، دیباگ آسان‌تر، آنتی‌ویروس کمتر حساس.



src.web و FastAPI از bundle حذف شده‌اند (فقط دسکتاپ).



مسیر data/ در runtime از get_data_path() می‌آید (کنار exe در حالت frozen).



قبل از توزیع عمومی: یک‌بار روی ماشین تمیز بدون Python تست کنید.

افزایش نسخه

فقط src/version.py و در صورت نیاز packaging/version_info.txt و #define MyAppVersion در installer.iss را هماهنگ کنید.