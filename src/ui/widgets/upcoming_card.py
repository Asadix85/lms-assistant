"""Upcoming Card: کارت رویداد نزدیک (رویداد یا مهلت)."""

from datetime import datetime

import jdatetime
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from src.models.event import Event, EventType
from src.models.assignment import Assignment
from src.ui.theme import CurrentTheme


class UpcomingCard(QFrame):
    """کارت رویداد/مهلت نزدیک با شمارش معکوس."""

    clicked = Signal(str)  # id

    def __init__(
        self,
        item: Event | Assignment,
        item_type: str,  # "event" یا "assignment"
        course_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item = item
        self._item_type = item_type
        self._course_name = course_name
        self._course_id = item.course_id or ""

        self.setObjectName("UpcomingCard")
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # === آیکون ===
        if self._item_type == "event":
            icon_text = "🎥"
            title = self._item.title
            time_text, color = self._get_event_time()
        else:
            icon_text = "📋"
            title = self._item.title
            time_text, color = self._get_assignment_time()

        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 18pt; background: transparent;")
        icon.setFixedWidth(32)
        layout.addWidget(icon)

        # === متن ===
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 600; font-size: 11pt; "
            "background: transparent;"
        )
        title_label.setAlignment(Qt.AlignRight)
        text_col.addWidget(title_label)

        sub_label = QLabel(self._course_name)
        sub_label.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; background: transparent;"
        )
        sub_label.setAlignment(Qt.AlignRight)
        text_col.addWidget(sub_label)

        layout.addLayout(text_col, stretch=1)

        # === زمان (راست) ===
        time_label = QLabel(time_text)
        time_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 11pt; "
            "background: transparent;"
        )
        time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        time_label.setMinimumWidth(90)
        layout.addWidget(time_label)

    def _get_event_time(self) -> tuple[str, str]:
        """زمان رویداد + رنگ."""
        c = CurrentTheme.colors()

        if not self._item.start_at:
            return "—", c.TEXT_MUTED

        delta = self._item.start_at - datetime.now()
        seconds = delta.total_seconds()

        if seconds < 0:
            return "گذشته", c.TEXT_MUTED
        elif seconds < 3600:  # کمتر از ۱ ساعت
            mins = int(seconds / 60)
            return f"{mins} دقیقه", c.ERROR
        elif seconds < 86400:  # کمتر از ۱ روز
            hours = int(seconds / 3600)
            return f"{hours} ساعت", c.WARNING
        else:
            days = int(seconds / 86400)
            return f"{days} روز", c.PRIMARY

    def _get_assignment_time(self) -> tuple[str, str]:
        """زمان مهلت + رنگ."""
        c = CurrentTheme.colors()

        if not self._item.deadline:
            return "—", c.TEXT_MUTED

        delta = self._item.deadline - datetime.now()
        seconds = delta.total_seconds()

        if seconds < 0:
            return "گذشته", c.ERROR
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} ساعت", c.ERROR
        elif seconds < 3 * 86400:
            days = int(seconds / 86400)
            return f"{days} روز", c.WARNING
        else:
            days = int(seconds / 86400)
            return f"{days} روز", c.SUCCESS

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._course_id)
        super().mousePressEvent(event)