#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.main_window import MainWindow
from src.ui.theme import Fonts, get_global_qss


def main() -> int:
    """اجرای برنامه."""
    app = QApplication(sys.argv)
    app.setApplicationName("LMS Assistant")

    # ⚠️ حیاتی: RTL سراسری در سطح QApplication
    # این خط باعث می‌شه همه‌ی widgetهای برنامه به‌طور خودکار RTL بشن
    app.setLayoutDirection(Qt.RightToLeft)

    # بارگذاری فونت
    Fonts.load()

    # اعمال QSS
    app.setStyleSheet(get_global_qss())

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())