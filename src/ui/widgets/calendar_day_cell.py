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
from src.ui.theme import CurrentTheme
from src.ui.widgets.calendar_event_item import CalendarEventItem


class CalendarDayCell(QFrame):
    """سلول یک روز از تقویم."""

    day_clicked = Signal(object)
    event_clicked = Signal(str)

    def __init__(self, jalali_date, assignments, is_today=False, is_selected=False, parent=None):
        super().__init__(parent)
        self._jalali_date = jalali_date
        self._assignments = assignments
        self._is_today = is_today
        self._is_selected = is_selected
        self.setObjectName("CalendarDayCell")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        weekday = self._jalali_date.strftime("%A")
        day_num = self._jalali_date.day

        header = QLabel(f"{weekday} {day_num}")
        header.setObjectName("DayLabel")
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(24)
        layout.addWidget(header)

        if self._assignments:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setSpacing(3)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setAlignment(Qt.AlignTop)

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
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        if self._is_today:
            border_color = c.PRIMARY
            border_width = 3
            bg = "rgba(96, 165, 250, 0.15)" if is_dark else "rgba(59, 130, 246, 0.08)"
        elif self._is_selected:
            border_color = c.PRIMARY
            border_width = 3
            bg = "rgba(96, 165, 250, 0.18)" if is_dark else "rgba(59, 130, 246, 0.1)"
        else:
            border_color = c.GLASS_BORDER
            border_width = 1
            bg = c.GLASS_BG

        # رنگ متن روز
        if self._is_today or self._is_selected:
            day_text_color = c.PRIMARY
            day_bg = "rgba(96, 165, 250, 0.25)" if is_dark else "rgba(59, 130, 246, 0.12)"
        else:
            day_text_color = c.TEXT_PRIMARY
            day_bg = c.GLASS_BG_HOVER

        self.setStyleSheet(f"""
            QFrame#CalendarDayCell {{
                background-color: {bg};
                border: {border_width}px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#CalendarDayCell:hover {{
                border-color: {c.PRIMARY};
            }}
            QLabel#DayLabel {{
                color: {day_text_color};
                font-weight: bold;
                font-size: 10pt;
                background-color: {day_bg};
                border-radius: 6px;
                padding: 3px;
            }}
            QLabel#DayEmpty {{
                color: {c.TEXT_MUTED};
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