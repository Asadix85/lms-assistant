"""Calendar Day Cell: سلول یک روز از تقویم."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from src.models.assignment import Assignment
from src.ui.theme import Colors
from src.ui.widgets.calendar_event_item import CalendarEventItem


class CalendarDayCell(QFrame):
    """سلول یک روز از تقویم."""

    day_clicked = Signal(object)
    event_clicked = Signal(str)

    def __init__(
        self,
        jalali_date,
        assignments: list[Assignment],
        is_today: bool = False,
        is_selected: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._jalali_date = jalali_date
        self._assignments = assignments
        self._is_today = is_today
        self._is_selected = is_selected
        self.setObjectName("CalendarDayCell")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        layout.setDirection(QVBoxLayout.TopToBottom)

        # === Header ===
        weekday = self._jalali_date.strftime("%A")
        day_num = self._jalali_date.day

        header = QLabel(f"{weekday} {day_num}")
        header.setObjectName("DayLabel")
        header.setAlignment(Qt.AlignCenter)
        header.setLayoutDirection(Qt.RightToLeft)
        header.setFixedHeight(24)
        layout.addWidget(header)

        # === Items ===
        if self._assignments:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setLayoutDirection(Qt.RightToLeft)

            container = QWidget()
            container.setLayoutDirection(Qt.RightToLeft)

            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(3)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignTop)
            container_layout.setDirection(QVBoxLayout.TopToBottom)

            for a in self._assignments:
                item = CalendarEventItem(a)
                item.clicked.connect(self.event_clicked.emit)
                container_layout.addWidget(item)

            scroll.setWidget(container)
            layout.addWidget(scroll, stretch=1)
        else:
            empty = QLabel("—")
            empty.setObjectName("DayEmpty")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty, stretch=1)

        self._apply_style()

    def _apply_style(self) -> None:
        if self._is_today:
            border_color = Colors.PRIMARY
            border_width = 3
            bg = "#F0FCFC"
        elif self._is_selected:
            border_color = Colors.PRIMARY
            border_width = 3
            bg = "#E8F8F8"
        else:
            border_color = Colors.BORDER
            border_width = 1
            bg = Colors.BG_CARD

        self.setStyleSheet(f"""
            QFrame#CalendarDayCell {{
                background-color: {bg};
                border: {border_width}px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#CalendarDayCell:hover {{
                border-color: {Colors.PRIMARY};
            }}
            QLabel#DayLabel {{
                color: {Colors.PRIMARY if self._is_today else Colors.TEXT_PRIMARY};
                font-weight: bold;
                font-size: 10pt;
                background-color: {Colors.PRIMARY_LIGHT if self._is_today else Colors.BG_HOVER};
                border-radius: 4px;
                padding: 2px;
            }}
            QLabel#DayEmpty {{
                color: {Colors.TEXT_MUTED};
                font-size: 12pt;
                background: transparent;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        self.day_clicked.emit(self._jalali_date)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._apply_style()