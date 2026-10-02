"""Calendar Event Item: آیتم کوچک یک ددلاین در سلول تقویم."""

from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from src.models.assignment import Assignment
from src.ui.theme import Colors


class CalendarEventItem(QFrame):
    """آیتم کوچک یک ددلاین."""

    clicked = Signal(str)

    def __init__(self, assignment: Assignment, parent=None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("CalendarEventItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._build()
        self._apply_style()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # === ساعت ===
        if self._assignment.deadline:
            time_str = self._assignment.deadline.strftime("%H:%M")
            deadline_label = QLabel(f"{time_str}  ⏹️")
            deadline_label.setObjectName("CalEventDeadline")
            deadline_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(deadline_label)

        # === عنوان (کامل، با wordWrap) ===
        title = QLabel(self._assignment.title)
        title.setObjectName("CalEventTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight | Qt.AlignTop)
        # ⚠️ اجازه بده QLabel ارتفاع کامل بگیره
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        title.setToolTip(self._assignment.title)
        layout.addWidget(title)

    def _apply_style(self) -> None:
        color = self._get_color()

        self.setStyleSheet(f"""
            QFrame#CalendarEventItem {{
                background-color: {color}22;
                border-right: 3px solid {color};
                border-radius: 4px;
            }}
            QFrame#CalendarEventItem:hover {{
                background-color: {color}44;
            }}
            QLabel#CalEventTitle {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#CalEventDeadline {{
                color: {color};
                font-size: 7pt;
                font-weight: bold;
                background: transparent;
            }}
        """)

    def _get_color(self) -> str:
        if not self._assignment.deadline:
            return Colors.TEXT_MUTED

        now = datetime.now()
        delta = self._assignment.deadline - now

        if delta.total_seconds() < 0:
            return Colors.TEXT_MUTED
        elif delta.days == 0:
            return Colors.ERROR
        elif delta.days == 1:
            return Colors.ACCENT
        elif delta.days <= 3:
            return Colors.WARNING
        else:
            return Colors.SUCCESS

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._assignment.id)
        super().mousePressEvent(event)