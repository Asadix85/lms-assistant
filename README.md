# 🎓 LMS Assistant

دستیار شخصی LMS دانشگاه اصفهان — همگام‌سازی دروس، تکالیف، رویدادها و اخبار از سامانه‌های `lms4.ui.ac.ir` و `quera.ui.ac.ir` با رابط گرافیکی دسکتاپ (PySide6)، CLI و ربات تلگرام.

## ✨ قابلیت‌ها
- احراز هویت خودکار و نگهداری Session در LMS و کوئرا
- همگام‌سازی دروس، محتواها، تکالیف، تقویم و تالارهای گفتگو
- ذخیره‌سازی محلی SQLite با سیستم مهاجرت Schema
- یادآوری ددلاین و خلاصه‌ی روزانه از طریق GitHub Actions + تلگرام
- رابط گرافیکی راست‌به‌چپ با تم روشن/تاریخ

## 🚀 نصب و اجرا

```bash
# نصب وابستگی‌های پایه + توسعه
pip install -e ".[dev]"

# برای رابط گرافیکی
pip install -e ".[gui]"

# کپی فایل نمونه‌ی تنظیمات
cp .env.example .env   # سپس مقادیر را پر کنید
```

### اجرا
```bash
python main.py          # رابط گرافیکی
python main.py --cli    # رابط فرمانی
```

## 🧪 تست و کیفیت کد
```bash
pytest tests -q         # اجرای تست‌ها
ruff check src config   # لینتر
mypy src                # بررسی نوع
```

CI از طریق GitHub Actions به‌صورت خودکار lint و تست را روی هر push/PR اجرا می‌کند.

## 🔐 امنیت
- فایل `.env` حاوی نام کاربری/رمز عبور است و **هرگز** نباید commit شود (در `.gitignore` لحاظ شده).
- سرویس `GitPusher` فقط `data/lms.db` را به‌صورت whitelist push می‌کند.
- داده‌های خام debug (`debug_*.html`, `data/*.html`) حاوی اطلاعات شخصی هستند؛ آن‌ها را در مخزن عمومی قرار ندهید.

## 📁 ساختار پروژه
```
config/        تنظیمات و ثابت‌ها
src/core/      احراز هویت، کلاینت HTTP، استثناها
src/collectors جمع‌آوری داده از صفحات LMS
src/parsers/   تحلیل HTML
src/models/    مدل‌های داده
src/storage/   دیتابیس + repositories + مهاجرت‌ها
src/services/  هماهنگی sync، اعلان‌ها، Git push
src/ui/        رابط گرافیکی PySide6
scripts/       ورودی‌های CLI/GUI/Bot و ابزارهای کمکی
tests/         تست‌های واحد
.github/       Workflow های زمان‌بندی‌شده و CI
```

## ⏰ یادداشت Cron
GitHub Actions ممکن است زمان‌بندی را چند دقیقه تا چند ساعت با تأخیر اجرا کند (به‌ویژه روی شاخه‌های کم‌فعالیت). برای ددلاین‌های حساس، از `workflow_dispatch` دستی یا یک trigger خارجی (مثل cron-job.org) استفاده کنید.
