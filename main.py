"""LMS Assistant - Entry Point.

نقطه‌ی ورود پروژه: با `python main.py` می‌توانید GUI یا CLI را اجرا کنید.

Usage:
    python main.py            # اجرای رابط گرافیکی (پیش‌فرض)
    python main.py --cli      # اجرای رابط فرمانی (Typer)
"""

import argparse
import sys


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
        "--cli", action="store_true", help="اجرای رابط فرمانی به‌جای GUI"
    )
    args, extra = parser.parse_known_args()

    if args.cli:
        sys.argv = [sys.argv[0], *extra]
        run_cli()
        return 0

    try:
        return run_gui()
    except ImportError as e:
        print(f"❌ برای اجرای GUI، وابستگی‌های gui را نصب کنید: pip install -e '.[gui]'")
        print(f"   جزئیات: {e}")
        print("   یا از رابط فرمانی استفاده کنید: python main.py --cli")
        return 1


if __name__ == "__main__":
    sys.exit(main())
