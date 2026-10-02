#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.settings_manager import SettingsManager
from src.ui.main_window import MainWindow
from src.ui.theme import Fonts, get_global_qss, CurrentTheme, ThemeMode


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LMS Assistant")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")

    Fonts.load()

    # ⚠️ بازیابی تم ذخیره‌شده
    saved_theme = SettingsManager.load_theme(default=ThemeMode.LIGHT)
    CurrentTheme.set_mode(saved_theme)
    print(f"🎨 تم بازیابی‌شده: {saved_theme}")

    # ⚠️ پاک کردن کش آیکون‌ها قبل از ساخت پنجره
    from src.ui.icons import Icons
    Icons.clear_cache()

    app.setStyleSheet(get_global_qss(saved_theme))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())