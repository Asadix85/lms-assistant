<div dir="rtl">

# 🎓 دستیار LMS — دانشگاه اصفهان

**دستیار شخصی سامانه‌های آموزشی دانشگاه اصفهان** — همگام‌سازی خودکار دروس، تکالیف، رویدادها، اخبار و انجمن‌ها از `lms3/lms4/lms5.ui.ac.ir` و `quera.org`، با **رابط وب مدرن (پیش‌فرض)**، رابط گرافیکی دسکتاپ (PySide6)، رابط فرمانی (CLI) و ربات تلگرام.

[English version ↓](#-lms-assistant--university-of-isfahan)

---

## ✨ قابلیت‌ها

### 🔐 اتصال و احراز هویت
- ورود خودکار به LMS با نگهداری Session و **لاگین مجدد خودکار در پس‌زمینه** هنگام انقضای نشست
- پشتیبانی از چند دامنه (`lms3`, `lms4`, `lms5`) و همچنین ورود جداگانه به **کوئرا** (`quera.org`)
- ذخیره‌ی امن اعتبارنامه‌ها با **keyring** (مدیریت اعتبارنامه‌ی ویندوز / Secret Service) یا فایل `.env`
- رمزنگاری اسرار با **Fernet (AES)** و هش کردن رمز عبور حساب‌های وب

### 🔄 همگام‌سازی (Sync)
- دروس، محتواها، تکالیف (LMS + کوئرا)، رویدادها/امتحانات، تقویم هفتگی کلاس‌ها، اعضا و تالارهای گفتگو (Wall)
- تشخیص **تغییرات** (Changes) بین دو همگام‌سازی و ثبت تاریخچه
- پیشرفت زنده‌ی همگام‌سازی با **SSE** (`/api/sync/stream`) و پیام‌های خطای فارسیِ قابل‌فهم
- زمان‌بند **بکاپ‌گیری خودکار** دیتابیس (هر N ساعت، نگهداشت M نسخه در `data/backups/`)

### 🖥️ رابط وب (حالت پیش‌فرض)
- سرور **FastAPI** + فرانت‌اند HTML/CSS/JS راست‌به‌چپ (فونت وزیرمتن) در `web/`
- پنل کاربری: داشبورد، دروس، جزئیات درس، تقویم، رویدادها، تکالیف، تغییرات، تحلیل/آمار، تنظیمات تم روشن/تاریخ
- **احراز هویت چندکاربره** با Session کوکی‌محور، محدودیت نرخ ورود (Rate Limit)، ابطال همه‌ی نشست‌ها
- پنل **ادمین**: مدیریت کاربران/نقش‌ها، حالت نگهداشت، لاگ رسیدگی (Audit)، دانلود بکاپ
- سیستم **پشتیبانی/تیکت** داخلی
- خروجی **ICS تقویم** (`/api/calendar.ics`)، خروجی JSON داده‌ی کاربر، حذف حساب
- پراکسی `/jaam` برای لینک جلسات مجازی، سرو استاتیک assets و PWA (manifest + Service Worker)
- bootstrap خودکار یک حساب ادمین محلی (در `admin_credentials.txt`)

### 🤖 ربات تلگرام و اعلان‌ها
- ربات **aiogram 3** با دکمه‌های «امروز»، «هفته»، «کوئرا»، «پست‌ها»، «آمار»، «بروزرسانی»
- پشتیبانی از **Cloudflare Worker Proxy** برای عبور از فیلترینگ (`TELEGRAM_PROXY_URL`)
- اسکریپت‌های GitHub Actions: **خلاصه‌ی روزانه**، **یادآوری ددلاین** (۳ روز مانده) و **اعلان تغییرات** به تلگرام
- اعلان دسکتاپ (Notifier) برای نتایج همگام‌سازی

### 📦 سایر
- دیتابیس **SQLite** با سیستم **مهاجرت Schema** نسخه‌دار
- رابط گرافیکی **PySide6** (RTL، تم روشن/تاریخ، نمودار matplotlib) — حالت قدیمی
- CLI با **Typer + Rich**: دستورات `update`, `courses`, `contents`, `events`, `changes`, `status`
- بسته‌بندی **exe با PyInstaller** (`scripts/build_exe.py` + `LMSAssistant.spec`)
- خروجی **سایت استاتیک** برای GitHub Pages با رمزنگاری اختیاری AES-256-GCM (`scripts/export_static.py`)

---

## 🚀 نصب و اجرا

نیازمندی: **Python ‪≥ 3.11‬**

```bash
# ۱) نصب وابستگی‌های پایه + توسعه
pip install -e ".[dev]"

# ۲) بر اساس رابطی که می‌خواهید:
pip install -e ".[web]"    # رابط وب (پیش‌فرض main.py)
pip install -e ".[gui]"    # رابط گرافیکی PySide6
pip install -e ".[bot]"    # ربات تلگرام

# ۳) ساخت فایل تنظیمات
cp .env.example .env       # سپس مقادیر را پر کنید
```

### اجرا

```bash
python main.py             # رابط وب → http://127.0.0.1:8000 (مستندات API: /docs)
python main.py --web       # همان بالا (صریح)
python main.py --gui       # رابط گرافیکی PySide6 (قدیمی)
python main.py --cli       # رابط فرمانی Typer
python scripts/run_bot.py  # ربات تلگرام
```

### متغیرهای محیطی مهم (`.env`)

| متغیر | توضیح |
|---|---|
| `LMS_USERNAME` / `LMS_PASSWORD` | اعتبارنامه‌ی LMS (شماره دانشجویی/رمز) |
| `QUERA_USERNAME` / `QUERA_PASSWORD` | اعتبارنامه‌ی کوئرا |
| `LMS_BASE_URL` | آدرس LMS (پیش‌فرض `https://lms4.ui.ac.ir`) |
| `DB_PATH` | مسیر دیتابیس SQLite (پیش‌فرض `./data/lms.db`) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | توکن و چت ربات تلگرام |
| `TELEGRAM_PROXY_URL` | آدرس Cloudflare Worker برای عبور از فیلترینگ |
| `LMS_SECRET_KEY` | کلید رمزنگاری اسرار — **در production الزامی** |
| `LMS_ENV` | مقدار `production` باعث بررسی‌های سخت‌گیرانه‌ی امنیتی می‌شود |
| `LMS_COOKIE_SECURE` | فعال‌سازی سلف `Secure` روی کوکی نشست |
| `LMS_BACKUP_INTERVAL_HOURS` / `LMS_BACKUP_KEEP` | دوره و تعداد نگه‌داشتن بکاپ خودکار |
| `LMS_REVOKE_OTHER_SESSIONS` | ابطال نشست‌های دیگر هنگام ورود (پیش‌فرض روشن) |
| `LMS_CORS_ORIGINS` | مبدأهای CORS مجزا با کاما |
| `LOG_LEVEL` | سطح لاگ (loguru) |

---

## 🧪 تست و کیفیت کد

```bash
pytest tests -q         # اجرای تست‌ها
ruff check src config   # لینتر
mypy src                # بررسی نوع
```

CI در GitHub Actions به‌صورت خودکار **lint + تست + بررسی نشت `.env`** را روی هر push/PR اجرا می‌کند (`ci.yml`).

### ساخت فایل اجرایی ویندوز

```bash
python scripts/build_exe.py   # PyInstaller (onedir) → dist/LMSAssistant
```

---

## ⏰ اتوماسیون GitHub Actions

| Workflow | زمان‌بندی | کار |
|---|---|---|
| `daily-summary.yml` | هر روز ۰۳:۰۰ UTC | خلاصه‌ی امروز و فردا به تلگرام |
| `deadline-reminder.yml` | هر روز ۰۴:۳۰ UTC | یادآوری ددلاین‌های ۳ روز آینده |
| `telegram-notify.yml` | هر ۲ ساعت | ارسال تغییرات جدید LMS/کوئرا |
| `ci.yml` | push/PR | لینت، تست، اسکن راز |

> ⚠️ **یادداشت Cron:** GitHub Actions ممکن است زمان‌بندی را چند دقیقه تا چند ساعت با تأخیر اجرا کند (به‌ویژه روی شاخه‌های کم‌فعالیت). برای ددلاین‌های حساس، از `workflow_dispatch` دستی یا trigger خارجی (مثل cron-job.org) استفاده کنید.

---

## 🔐 امنیت

- فایل `.env` حاوی نام کاربری/رمز عبور است و **هرگز** نباید commit شود (در `.gitignore` لحاظ شده؛ CI هم کنترل می‌کند).
- اعتبارنامه‌ها در صورت وجود keyring، **امن** ذخیره می‌شوند؛ اسرار وب با Fernet رمزنگاری و توکن‌های نشست hash می‌شوند.
- endpointهای حساس (ورود) دارای **Rate Limit** پنجره‌ی لغزان هستند.
- سرویس `GitPusher` فقط `data/lms.db` را به‌صورت whitelist push می‌کند.
- داده‌های خام debug (`debug_*.html`, `data/*.html`) حاوی اطلاعات شخصی هستند؛ آن‌ها را در مخزن عمومی قرار ندهید.
- راهنمای بازیابی بکاپ: [`docs/RESTORE.md`](docs/RESTORE.md)

---

## 📁 ساختار پروژه

```
main.py            نقطه‌ی ورود (وب/GUI/CLI)
config/            تنظیمات (pydantic-settings) و ثابت‌ها
src/core/          احراز هویت LMS/Quera، کلاینت HTTP، استثناها
src/collectors/    جمع‌آوری داده از صفحات LMS (دروس، محتوا، رویداد، تالار، اعضا)
src/parsers/       تحلیل HTML (BeautifulSoup/lxml) + پارسر کوئرا و برنامه‌ی هفتگی
src/models/        مدل‌های داده (درس، تکلیف، رویداد، پست، تغییرات، …)
src/storage/       دیتابیس SQLite + repositories + مهاجرت Schema
src/services/      هماهنگی Sync، Quera Sync، اعلان‌ها، credentials، Git push
src/web/           سرور FastAPI: routers، session، security، بکاپ، ICS، پراکسی
src/ui/            رابط گرافیکی PySide6 (صفحات، ویجت‌ها، تم RTL)
web/               فرانت‌اند وب (HTML/CSS/JS، PWA)
scripts/           ورودی‌های run_web/run_gui/run_cli/bot + ابزارها و دیباگ‌ها
tests/             تست‌های واحد (pytest)
.github/workflows/ CI و زمان‌بندی‌های تلگرام
assets/            آیکون‌ها و فونت وزیرمتن
docs/              مستندات (بازیابی بکاپ)
```

---

## ❓ سؤالات پرتکرار

**ورود به LMS ناموفق است؟** نشانه‌ی `LMS_USERNAME/LMS_PASSWORD` را در `.env` بررسی کنید؛ سامانه‌ی LMS4 گاهی کپچا/تأخیر دارد — برنامه تلاش مجدد خودکار دارد.

**ربات وصل نمی‌شود؟** اگر از داخل ایران اجرا می‌کنید، `TELEGRAM_PROXY_URL` (Cloudflare Worker) را ست کنید.

**دیتابیس خراب شد؟** بکاپ‌های خودکار در `data/backups/` هستند؛ مراحل بازگردانی در `docs/RESTORE.md`.

</div>

---

<a name="-lms-assistant--university-of-isfahan"></a>

# 🎓 LMS Assistant — University of Isfahan

**A personal assistant for the University of Isfahan educational systems** — automatically syncs courses, assignments, events, news and forums from `lms3/lms4/lms5.ui.ac.ir` and `quera.org`, with a **modern web UI (default)**, a PySide6 desktop GUI, a CLI and a Telegram bot.

[فارسی ↑](#-دستیار-lms--دانشگاه-اصفهان)

---

## ✨ Features

### 🔐 Connection & Authentication
- Automatic LMS login with session persistence and **background re-login** when the session expires
- Multi-domain support (`lms3`, `lms4`, `lms5`) plus separate **Quera** (`quera.org`) authentication
- Secure credential storage via **keyring** (Windows Credential Manager / Secret Service) or `.env`
- Secrets encrypted with **Fernet (AES)**; web account passwords hashed

### 🔄 Sync
- Courses, contents, assignments (LMS + Quera), events/exams, weekly class schedule, members and discussion walls
- **Change detection** between syncs with history
- Live sync progress over **SSE** (`/api/sync/stream`) with human-readable error messages
- **Automatic database backups** on a scheduler (every N hours, keeps M copies in `data/backups/`)

### 🖥️ Web Interface (default mode)
- **FastAPI** backend + RTL HTML/CSS/JS frontend (Vazirmatn font) in `web/`
- User panel: dashboard, courses, course detail, calendar, events, assignments, changes, analytics, light/dark theme settings
- **Multi-user authentication** with cookie-based sessions, login rate limiting, revoke-all-sessions
- **Admin panel**: user/role management, maintenance mode, audit log, backup download
- Built-in **support/ticket system**
- **ICS calendar export** (`/api/calendar.ics`), JSON data export, account deletion
- `/jaam` proxy for virtual-class links, static asset serving, PWA (manifest + Service Worker)
- Automatic bootstrap of a local admin account (written to `admin_credentials.txt`)

### 🤖 Telegram Bot & Notifications
- **aiogram 3** bot with buttons: "Today", "Week", "Quera", "Posts", "Stats", "Refresh"
- **Cloudflare Worker proxy** support to bypass filtering (`TELEGRAM_PROXY_URL`)
- GitHub Actions scripts: **daily summary**, **deadline reminders** (3 days ahead) and **change notifications** via Telegram
- Desktop notifications (Notifier) for sync results

### 📦 More
- **SQLite** database with versioned **schema migrations**
- **PySide6** desktop GUI (RTL, light/dark theme, matplotlib charts) — legacy mode
- **Typer + Rich** CLI: `update`, `courses`, `contents`, `events`, `changes`, `status`
- **PyInstaller** exe packaging (`scripts/build_exe.py` + `LMSAssistant.spec`)
- **Static site export** for GitHub Pages with optional AES-256-GCM encryption (`scripts/export_static.py`)

---

## 🚀 Installation & Run

Requires **Python ≥ 3.11**

```bash
# 1) Install base + dev dependencies
pip install -e ".[dev]"

# 2) Depending on the interface you want:
pip install -e ".[web]"    # Web UI (default for main.py)
pip install -e ".[gui]"    # PySide6 desktop GUI
pip install -e ".[bot]"    # Telegram bot

# 3) Create settings file
cp .env.example .env       # then fill in your values
```

### Run

```bash
python main.py             # Web UI → http://127.0.0.1:8000 (API docs: /docs)
python main.py --web       # same as above (explicit)
python main.py --gui       # PySide6 desktop GUI (legacy)
python main.py --cli       # Typer CLI
python scripts/run_bot.py  # Telegram bot
```

### Key environment variables (`.env`)

| Variable | Description |
|---|---|
| `LMS_USERNAME` / `LMS_PASSWORD` | LMS credentials (student ID / password) |
| `QUERA_USERNAME` / `QUERA_PASSWORD` | Quera credentials |
| `LMS_BASE_URL` | LMS URL (default `https://lms4.ui.ac.ir`) |
| `DB_PATH` | SQLite database path (default `./data/lms.db`) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Bot token and chat id |
| `TELEGRAM_PROXY_URL` | Cloudflare Worker URL to bypass filtering |
| `LMS_SECRET_KEY` | Encryption key for secrets — **required in production** |
| `LMS_ENV` | Setting it to `production` enables strict security checks |
| `LMS_COOKIE_SECURE` | Enable the `Secure` flag on session cookies |
| `LMS_BACKUP_INTERVAL_HOURS` / `LMS_BACKUP_KEEP` | Backup interval and retention count |
| `LMS_REVOKE_OTHER_SESSIONS` | Revoke other sessions on login (on by default) |
| `LMS_CORS_ORIGINS` | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | Logging level (loguru) |

---

## 🧪 Testing & Code Quality

```bash
pytest tests -q         # run tests
ruff check src config   # linter
mypy src                # type checking
```

GitHub Actions CI automatically runs **lint + tests + `.env` leak check** on every push/PR (`ci.yml`).

### Building a Windows executable

```bash
python scripts/build_exe.py   # PyInstaller (onedir) → dist/LMSAssistant
```

---

## ⏰ GitHub Actions Automation

| Workflow | Schedule | Purpose |
|---|---|---|
| `daily-summary.yml` | Daily 03:00 UTC | Today + tomorrow summary to Telegram |
| `deadline-reminder.yml` | Daily 04:30 UTC | Remind deadlines within the next 3 days |
| `telegram-notify.yml` | Every 2 hours | Push new LMS/Quera changes to Telegram |
| `ci.yml` | push/PR | Lint, tests, secret scan |

> ⚠️ **Cron note:** GitHub Actions may delay scheduled runs by minutes to hours (especially on low-activity branches). For critical deadlines use manual `workflow_dispatch` or an external trigger (e.g. cron-job.org).

---

## 🔐 Security

- `.env` contains credentials and must **never** be committed (already in `.gitignore`; CI verifies this).
- Credentials are stored securely via keyring when available; web secrets are Fernet-encrypted and session tokens are hashed.
- Sensitive endpoints (login) use a **sliding-window rate limiter**.
- `GitPusher` only pushes `data/lms.db` via a whitelist.
- Raw debug dumps (`debug_*.html`, `data/*.html`) contain personal data — do not put them in a public repository.
- Backup restore guide: [`docs/RESTORE.md`](docs/RESTORE.md)

---

## 📁 Project Structure

```
main.py            Entry point (Web / GUI / CLI)
config/            Settings (pydantic-settings) and constants
src/core/          LMS/Quera auth, HTTP clients, exceptions
src/collectors/    Data collectors for LMS pages (courses, contents, events, wall, members)
src/parsers/       HTML parsers (BeautifulSoup/lxml) + Quera & weekly-schedule parsers
src/models/        Data models (course, assignment, event, post, change, …)
src/storage/       SQLite database + repositories + schema migrations
src/services/      Sync orchestration, Quera sync, notifications, credentials, git push
src/web/           FastAPI server: routers, sessions, security, backups, ICS, proxy
src/ui/            PySide6 desktop GUI (pages, widgets, RTL theme)
web/               Web frontend (HTML/CSS/JS, PWA)
scripts/           run_web/run_gui/run_cli/bot entry points + tools & debug helpers
tests/             Unit tests (pytest)
.github/workflows/ CI and Telegram schedules
assets/            Icons and Vazirmatn font
docs/              Documentation (backup restore)
```

---

## ❓ FAQ

**LMS login fails?** Check `LMS_USERNAME/LMS_PASSWORD` in `.env`; LMS4 sometimes has delays/captcha — the app retries automatically.

**Bot won't connect?** If running from Iran, set `TELEGRAM_PROXY_URL` (Cloudflare Worker).

**Database corrupted?** Automatic backups live in `data/backups/`; see `docs/RESTORE.md` for the restore procedure.
