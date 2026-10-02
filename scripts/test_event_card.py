"""تست EventCard جداگانه."""

import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.theme import Fonts, get_global_qss
from src.models.event import Event, EventType
from src.ui.widgets.event_card import EventCard


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تست EventCard")
        self.resize(800, 300)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(get_global_qss())

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)

        # یک رویداد تست
        e = Event(
            id="test1",
            course_id="134345",
            title="ساختمان داده 03-جلسه 3",
            event_type=EventType.LIVE_SESSION,
            url="https://lms4.ui.ac.ir/jaam/joinfast/ABC/134",
            room_token="ABC",
            start_at=datetime(2026, 10, 2, 10, 0),
        )

        print("ساخت EventCard...")
        card = EventCard(e)
        print("EventCard ساخته شد ✅")
        layout.addWidget(card)

        layout.addStretch()


def main():
    app = QApplication(sys.argv)
    Fonts.load()
    window = TestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())