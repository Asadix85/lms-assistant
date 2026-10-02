#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.main_window import MainWindow
from src.ui.theme import Fonts, get_global_qss, CurrentTheme, ThemeMode


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LMS Assistant")
    app.setLayoutDirection(Qt.RightToLeft)

    # ⚠️ تنظیمات global برای شفافیت
    app.setStyle("Fusion")  # ← برای اینکه QSS یکنواخت اعمال بشه

    Fonts.load()
    CurrentTheme.set_mode(ThemeMode.LIGHT)
    app.setStyleSheet(get_global_qss(ThemeMode.LIGHT))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())