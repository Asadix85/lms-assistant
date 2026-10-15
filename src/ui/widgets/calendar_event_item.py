"""Calendar Event Item: آیتم کوچک یک ددلاین — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.models.assignment import Assignment
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CalendarEventItem(QFrame):
    """آیتم ددلاین با نوار رنگی بر اساس وضعیت."""

    clicked = Signal(str)

    def __init__(self, assignment: Assignment, parent=None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("CalendarEventItem")
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        # --- نوار رنگی سمت راست ---
        color_bar = QFrame()
        color_bar.setFixedWidth(4)
        color_bar.setStyleSheet(f"background-color: {self._get_status_color()}; border-radius: 2px;")
        lay.addWidget(color_bar)

        # --- محتوا ---
        content = QVBoxLayout()
        content.setSpacing(2)

        # زمان
        if self._assignment.deadline:
            time_str = self._assignment.deadline.strftime("%H:%M")
            time_lbl = QLabel(f"⏰ {time_str}")
            time_lbl.setStyleSheet(
                f"color: {self._get_status_color()}; font-size: 7.5pt; "
                "font-weight: 700; background: transparent;"
            )
            content.addWidget(time_lbl)

        # عنوان
        title = QLabel(self._assignment.title)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 8pt; "
            "font-weight: 600; background: transparent;"
        )
        content.addWidget(title)

        lay.addLayout(content, stretch=1)
        self._apply_style()

    def _get_status_color(self) -> str:
        if not self._assignment.deadline:
            return _c('TEXT_MUTED', '#8E8E93')

        now = datetime.now()
        delta = self._assignment.deadline - now

        if delta.total_seconds() < 0:
            return _c('TEXT_MUTED', '#8E8E93')
        elif delta.days == 0:
            return _c('ERROR', '#FF3B30')
        elif delta.days == 1:
            return _c('ACCENT', '#FF9500')
        elif delta.days <= 3:
            return _c('WARNING', '#FF9500')
        else:
            return _c('SUCCESS', '#34C759')

    def _apply_style(self) -> None:
        color = self._get_status_color()
        is_dark = CurrentTheme.is_dark()

        if is_dark:
            # ✅ پس‌زمینه تیره با tint رنگی برای دارک مود
            bg = f"{color}20"  # 20 = ~12% opacity
            bg_hover = f"{color}30"
            border = f"{color}40"
        else:
            bg = "#FFFFFF"
            bg_hover = "#F8F9FA"
            border = "rgba(0,0,0,0.06)"

        self.setStyleSheet(f"""
            QFrame#CalendarEventItem {{
                background-color: {bg};
                border-radius: 6px;
                border: 1px solid {border};
            }}
            QFrame#CalendarEventItem:hover {{
                background-color: {bg_hover};
                border-color: {color}60;
            }}
        """)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._assignment.id)
        super().mousePressEvent(event)