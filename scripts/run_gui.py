#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QLocale, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.settings_manager import SettingsManager
from src.ui.main_window import MainWindow
from src.ui.theme import Fonts, get_global_qss, CurrentTheme, ThemeMode


def main() -> int:
    # ۱. لوکال فارسی
    QLocale.setDefault(QLocale(QLocale.Persian, QLocale.Iran))

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icons/app.ico"))
    app.setApplicationName("LMS Assistant")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")

    Fonts.load()

    saved_theme = SettingsManager.load_theme(default=ThemeMode.LIGHT)
    CurrentTheme.set_mode(saved_theme)
    print(f"🎨 تم بازیابی‌شده: {saved_theme}")

    from src.ui.icons import Icons
    Icons.clear_cache()

    app.setStyleSheet(get_global_qss(saved_theme))

    window = MainWindow()
    window.show()

    print(f"🧭 جهت اپلیکیشن: {app.layoutDirection()}")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())