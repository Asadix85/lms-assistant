#!/usr/bin/env bash
# جابه‌جایی داده‌های خام debug از مخزن (این اسکریپت را محلی اجرا کنید، نه در CI)
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p ../lms-debug-data/html ../lms-debug-data/db

# ۱. حذف فایل‌های HTML خام از Git (نگهداری lms.db تا زمانی که Actions به آن وابسته است)
git rm --cached data/*.html debug_*.html 2>/dev/null || true
echo "data/*.html" >> .gitignore
echo "debug_*.html.bak" >> .gitignore

# ۲. کپی فایل‌ها به بیرون از مخزن برای استفاده‌ی محلی
cp -n data/*.html ../lms-debug-data/html/ 2>/dev/null || true
cp -n debug_*.html ../lms-debug-data/html/ 2>/dev/null || true

echo "✅ فایل‌های debug از index خارج شدند و در ../lms-debug-data ذخیره شدند."
echo "⚠️ برای پاک‌سازی کامل تاریخچه: git filter-repo --path data/ --path debug_calendar.html ... --invert-paths"
echo "   سپس force-push کنید و رمز تلگرام/سشن‌ها را در صورت نشتی rotate نمایید."
