"""ساخت EXE با PyInstaller."""

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
APP_NAME = "LMSAssistant"


def clean() -> None:
    """پاکسازی build های قبلی."""
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"🗑️  پاک شد: {d}")

    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        spec.unlink()
        print(f"🗑️  پاک شد: {spec}")


def build() -> None:
    """Build با PyInstaller."""
    print("🔨 شروع build...")

    # آرگومان‌های PyInstaller
    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",              # پوشه‌ی کامل (نه فایل تنها)
        "--console",             # ← با console (برای debug)
        "--noconfirm",           # بدون پرسش
        "--clean",               # پاکسازی cache

        # آیکون
        "--icon", str(ROOT / "assets" / "icons" / "app.ico"),

        # assets رو **کپی نکن** — خودمون در post_build کپی می‌کنیم
        "--add-data", f"{ROOT / 'src' / 'storage' / 'schema.sql'};src/storage",

        # hidden imports
        "--hidden-import", "keyring.backends.Windows",
        "--hidden-import", "keyring.backends.SecretService",
        "--hidden-import", "keyring.backends.kwallet",
        "--hidden-import", "aiogram",
        "--hidden-import", "jdatetime",
        "--hidden-import", "matplotlib.backends.backend_qtagg",

        # entry point
        str(ROOT / "scripts" / "run_gui.py"),
    ]

    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        print("❌ Build failed")
        sys.exit(1)

    print("✅ Build موفق")


def post_build() -> None:
    """کپی assets, data, .env.example کنار EXE."""
    app_dir = DIST_DIR / APP_NAME
    if not app_dir.exists():
        print(f"❌ {app_dir} پیدا نشد")
        return

    # === کپی assets ===
    print("📦 کپی assets...")
    src_assets = ROOT / "assets"
    dst_assets = app_dir / "assets"
    if src_assets.exists():
        if dst_assets.exists():
            shutil.rmtree(dst_assets)
        shutil.copytree(src_assets, dst_assets)
        print(f"  ✅ {dst_assets}")

    # === کپی data (اگه دیتابیس هست) ===
    print("📦 کپی data...")
    dst_data = app_dir / "data"
    dst_data.mkdir(exist_ok=True)

    src_db = ROOT / "data" / "lms.db"
    if src_db.exists():
        shutil.copy2(src_db, dst_data / "lms.db")
        print(f"  ✅ lms.db کپی شد")
    else:
        print(f"  ⚠️ lms.db توی پروژه نیست — اولین اجرا sync کن")

    # پوشه‌ی files
    (dst_data / "files").mkdir(exist_ok=True)
    print(f"  ✅ {dst_data}")

    # === کپی .env.example ===
    print("📦 کپی .env.example...")
    src_env = ROOT / ".env.example"
    if src_env.exists():
        shutil.copy(src_env, app_dir / ".env.example")
        print(f"  ✅ .env.example")

    # === کپی README ===
    readme_content = """LMS Assistant
=============

نصب و اجرا:
1. فایل .env.example رو به .env تغییر نام بده
2. اطلاعات LMS و Quera رو توی .env پر کن
3. LMSAssistant.exe رو اجرا کن

نکته:
- اولین اجرا، Login Dialog باز می‌شه
- اطلاعات ورود به‌صورت امن در Windows Credential Manager ذخیره می‌شه

پشتیبانی:
- GitHub: https://github.com/Asadix85/lms-assistant
"""
    (app_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    print(f"  ✅ README.txt")


def main() -> None:
    clean()
    build()
    post_build()

    app_dir = DIST_DIR / APP_NAME
    print(f"\n🎉 EXE ساخته شد: {app_dir}")
    print(f"   فایل اجرایی: {app_dir / (APP_NAME + '.exe')}")
    print(f"\n📝 یادآوری:")
    print(f"   - .env.example → .env (ویرایش کن)")
    print(f"   - assets/ و data/ کنار EXE هستن")


if __name__ == "__main__":
    main()