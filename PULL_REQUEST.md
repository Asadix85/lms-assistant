# Pull Request: رفع باگ‌های بنیادین + زیرساخت RTL + دکمه انتشار

**Branch:** `qwen-code-2356e6e7-b971-4e6a-b57d-aadc08e16db9` → `master`
**Commits:** 6 | **Files:** 44 (+1022 / −290)

## خلاصه
مجموعه تغییرات شامل اصلاحات امنیتی/کیفی کد، رفع باگ رفرش تم، راه‌اندازی کامل RTL فارسی (با رفع رانتایم PySide6)، دکمه «انتشار GitHub» در Header و CI workflow.

## لیست کامیت‌ها (به ترتیب)
1. `7e35b9f` fix: تکمیل وابستگی‌ها، منطق Retry (فقط 429/5xx)، whitelist گیتمین GitPusher، سیستم Migration، CI workflow، نقطه ورود CLI/GUI، README
2. `c713ddf` fix(ui): رفع باگ nested class و عدم رفرش تم در MainWindow / AnalyticsPage / CourseDetailPage
3. `cbac107` feat(rtl): زیرساخت متمرکز سه‌لایه RTL — ماژول `src/ui/rtl.py` (EventFilter سطح اپ + `RTLWidgetMixin` روی ۲۰ ویجت + پاک‌سازی بازگشتی با حفظ AlignCenter و `mark_ltr`)
4. `b263bd4` fix(rtl): رفع `TypeError` در `QBoxLayout.setDirection` (استفاده از `setLayoutDirection`)
5. `347407b` feat(ui): دکمه «🚀 انتشار» در Header + `PublishWorker` (push در thread جدا) + skip تست‌های integration بدون credentials
6. `0181c86` chore: حذف فایل‌های `.pyc` از ردیابی git

## نحوه اعمال روی مخزن شما
```bash
git checkout -b feature/review-fixes-and-rtl master
git am patches/*.patch        # یا: git checkout <branch-name>
```
اگر `git am` به دلیل تفاوت خط‌پایانی (CRLF ویندوز) شکست خورد:
```bash
git am --whitespace=fix patches/*.patch
```

## تست‌شده ✅
- `pytest`: 5 passed, 8 skipped (integration test‌ها بدون credentials skip می‌شوند)
- اجرای GUI بدون Traceback پس از رفع `b263bd4`
- Migration: دیتابیس بدون نسخه → `schema_version=1` به‌صورت خودکار

## بازنگری‌کنندگان باید چک کنند
- [ ] رفتار دکمه انتشار با remote واقعی (`git remote -v`)
- [ ] نمایش کارت‌های داینامیک بعد از Sync در حالت RTL
- [ ] فیلد Chat ID تلگرام همچنان LTR بماند
