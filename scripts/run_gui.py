#!/usr/bin/env python
"""LMS Assistant GUI."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# اضافه کردن ریشه پروژه به sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.main_window import MainWindow


def main() -> int:
    """اجرای برنامه."""
    app = QApplication(sys.argv)
    app.setApplicationName("LMS Assistant")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())