"""تست خالص PySide6 بدون پروژه."""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFrame, QHBoxLayout, QLabel, QWidget
)
from PySide6.QtCore import Qt


class PureTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تست خالص")
        self.resize(400, 200)

        central = QWidget()
        self.setCentralWidget(central)

        outer = QHBoxLayout(central)
        print("1. outer layout ✅")

        # یک QFrame داخل layout
        frame = QFrame()
        frame.setObjectName("TestFrame")
        frame.setMinimumHeight(100)

        print("2. QFrame ساخته شد ✅")

        # ⚠️ خط بحرانی:
        inner = QHBoxLayout(frame)
        print("3. QHBoxLayout(frame) ✅")

        label = QLabel("سلام")
        inner.addWidget(label)

        outer.addWidget(frame)
        print("4. همه چیز ✅")


def main():
    app = QApplication(sys.argv)
    w = PureTest()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())