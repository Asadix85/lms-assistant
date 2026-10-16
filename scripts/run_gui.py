#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.credential_provider import CredentialProvider
from src.services.settings_manager import SettingsManager
from src.ui.main_window import MainWindow
from src.ui.theme import Fonts, get_global_qss, CurrentTheme, ThemeMode


def main() -> int:
    QLocale.setDefault(QLocale(QLocale.Persian, QLocale.Iran))

    app = QApplication(sys.argv)
    app.setApplicationName("LMS Assistant")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")

    # === RTL: فیلتر سطح-اپلیکیشن + ترجمه رسمی Qt فارسی ===
    # هر ویجت تازه‌ساخته‌شده (کارت‌های داینامیک بعد از همگام‌سازی، دیالوگ‌ها،
    # Toast و...) خودکار RTL می‌شود؛ نیازی به فراخوانی دستی نیست.
    from src.ui.rtl import install_rtl_event_filter, load_qt_translations

    install_rtl_event_filter(app)
    load_qt_translations(app)

    Fonts.load()

    saved_theme = SettingsManager.load_theme(default=ThemeMode.LIGHT)
    CurrentTheme.set_mode(saved_theme)
    print(f"🎨 تم بازیابی‌شده: {saved_theme}")

    from src.ui.icons import Icons
    Icons.clear_cache()

    app.setStyleSheet(get_global_qss(saved_theme))

    # === بارخوانی credentials ===
    creds = CredentialProvider.load()

    # === اگه LMS نبود، Dialog باز کن ===
    if not creds.lms_username or not creds.lms_password:
        print("🔐 Login Dialog باز می‌شود...")

        from src.ui.dialogs.login_dialog import LoginDialog

        dialog = LoginDialog(
            lms_username=creds.lms_username,
            lms_password=creds.lms_password,
            quera_username=creds.quera_username,
            quera_password=creds.quera_password,
        )

        # اتصال signal
        dialog.login_success.connect(
            lambda lu, lp, qu, qp: CredentialProvider.update(lu, lp, qu, qp)
        )

        if dialog.exec() != LoginDialog.Accepted:
            print("❌ کاربر انصراف داد")
            return 0

        print("✅ اطلاعات وارد شد")

    window = MainWindow()
    window.show()

    print(f"🧭 جهت اپلیکیشن: {app.layoutDirection()}")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())