"""LMS Assistant - Entry Point.

نقطه‌ی ورود پروژه: با `python main.py` می‌توانید GUI یا CLI را اجرا کنید.

Usage:
    python main.py            # اجرای رابط وب (پیش‌فرض)
    python main.py --web      # اجرای رابط وب (FastAPI + HTML/CSS)
    python main.py --gui      # اجرای رابط گرافیکی PySide6 (قدیمی)
    python main.py --cli      # اجرای رابط فرمانی (Typer)
"""

import argparse
import sys


def run_web() -> None:
    """اجرای رابط وب (FastAPI + HTML/CSS)."""
    from scripts.run_web import main as web_main

    web_main()


def run_gui() -> int:
    """اجرای رابط گرافیکی PySide6."""
    from scripts.run_gui import main as gui_main

    return gui_main()


def run_cli() -> None:
    """اجرای رابط فرمانی Typer."""
    from scripts.run_cli import app

    app()


def main() -> int:
    parser = argparse.ArgumentParser(description="LMS Assistant")
    parser.add_argument(
        "--cli", action="store_true", help="اجرای رابط فرمانی به‌جای رابط وب"
    )
    parser.add_argument(
        "--gui", action="store_true", help="اجرای رابط گرافیکی قدیمی (PySide6)"
    )
    parser.add_argument(
        "--web", action="store_true", help="اجرای رابط وب (پیش‌فرض)"
    )
    args, extra = parser.parse_known_args()

    if args.cli:
        sys.argv = [sys.argv[0], *extra]
        run_cli()
        return 0

    if args.gui:
        try:
            return run_gui()
        except ImportError as e:
            print("❌ برای اجرای GUI، وابستگی‌های gui را نصب کنید: pip install -e '.[gui]'")
            print(f"   جزئیات: {e}")
            return 1

    # پیش‌فرض: رابط وب
    try:
        run_web()
        return 0
    except ImportError as e:
        print("❌ برای اجرای رابط وب، وابستگی‌های web را نصب کنید: pip install -e '.[web]'")
        print(f"   جزئیات: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
