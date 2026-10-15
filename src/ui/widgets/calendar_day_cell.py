"""Calendar Day Cell: سلول یک روز از تقویم — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget, QHBoxLayout,
)

from src.models.assignment import Assignment
from src.ui.theme import CurrentTheme
from src.ui.widgets.calendar_event_item import CalendarEventItem


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CalendarDayCell(QFrame):
    """سلول یک روز با افکت شیشه‌ای و نشانگر امروز."""

    day_clicked = Signal(object)
    event_clicked = Signal(str)

    WEEKDAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]

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
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # --- هدر روز ---
        weekday = self.WEEKDAYS[self._jalali_date.weekday()]
        day_num = self._jalali_date.day

        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        day_lbl = QLabel(str(day_num))
        day_lbl.setAlignment(Qt.AlignCenter)
        day_lbl.setFixedSize(32, 32)
        day_lbl.setStyleSheet(self._day_number_style())
        header_row.addWidget(day_lbl)

        weekday_lbl = QLabel(weekday)
        weekday_lbl.setStyleSheet(self._weekday_style())
        header_row.addWidget(weekday_lbl, stretch=1)

        if self._is_today:
            today_dot = QLabel("•")
            today_dot.setStyleSheet(f"color: {_c('PRIMARY', '#2AA6A3')}; font-size: 16pt; font-weight: bold;")
            header_row.addWidget(today_dot)

        lay.addLayout(header_row)

        # --- لیست رویدادها ---
        if self._assignments:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

            container = QWidget()
            container_lay = QVBoxLayout(container)
            container_lay.setSpacing(4)
            container_lay.setContentsMargins(0, 0, 0, 0)
            container_lay.setAlignment(Qt.AlignTop)

            for a in self._assignments[:5]:  # حداکثر ۵ تا
                item = CalendarEventItem(a)
                item.clicked.connect(self.event_clicked.emit)
                container_lay.addWidget(item)

            if len(self._assignments) > 5:
                more = QLabel(f"+{len(self._assignments) - 5} مورد دیگر")
                more.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 7.5pt; background: transparent;")
                more.setAlignment(Qt.AlignCenter)
                container_lay.addWidget(more)

            scroll.setWidget(container)
            lay.addWidget(scroll, stretch=1)
        else:
            empty = QLabel("—")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 14pt; background: transparent;")
            lay.addWidget(empty, stretch=1)

        self._apply_style()

    def _day_number_style(self) -> str:
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        if self._is_today:
            return f"""
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_DARK});
                color: #FFFFFF; border-radius: 16px; font-size: 11pt; font-weight: 800;
            """
        elif self._is_selected:
            if is_dark:
                bg = "rgba(42, 166, 163, 0.30)"
                color = "#4ECDC4"  # روشن‌تر برای دارک
            else:
                bg = "rgba(42, 166, 163, 0.15)"
                color = c.PRIMARY
            return f"""
                background-color: {bg};
                color: {color}; border-radius: 16px; font-size: 11pt; font-weight: 800;
            """
        else:
            if is_dark:
                # ✅ تیره با متن روشن برای دارک مود
                return """
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #EBEBF5; border-radius: 16px; font-size: 11pt; font-weight: 700;
                """
            else:
                return """
                    background-color: #F8F9FA;
                    color: #1C1C1E; border-radius: 16px; font-size: 11pt; font-weight: 700;
                    border: 1px solid rgba(0, 0, 0, 0.08);
                """

    def refresh_theme(self) -> None:
        """بعد از تغییر تم صدا زده بشه."""
        self._apply_style()
        # به‌روزرسانی استایل شماره روز
        for child in self.findChildren(QLabel):
            if child.text().isdigit() and len(child.text()) <= 2:
                child.setStyleSheet(self._day_number_style())
                break
        # به‌روزرسانی استایل weekday
        for child in self.findChildren(QLabel):
            if not child.text().isdigit() and child.text() in self.WEEKDAYS:
                child.setStyleSheet(self._weekday_style())
                break

    def _weekday_style(self) -> str:
        color = _c('PRIMARY', '#2AA6A3') if (self._is_today or self._is_selected) else _c('TEXT_SECONDARY', '#3A3A3C')
        return f"color: {color}; font-size: 8.5pt; font-weight: 600; background: transparent;"

    def _apply_style(self) -> None:
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        if self._is_today:
            border_color = c.PRIMARY
            border_width = 2
            if is_dark:
                bg = "rgba(42, 166, 163, 0.18)"  # تیره‌تر برای دارک
            else:
                bg = "rgba(42, 166, 163, 0.08)"
        elif self._is_selected:
            border_color = c.PRIMARY
            border_width = 2
            if is_dark:
                bg = "rgba(42, 166, 163, 0.22)"
            else:
                bg = "rgba(42, 166, 163, 0.10)"
        else:
            border_color = c.GLASS_BORDER
            border_width = 1
            if is_dark:
                bg = "rgba(28, 38, 38, 0.75)"  # ✅ تیره برای دارک مود
            else:
                bg = "#FFFFFF"

        hover_bg = "rgba(42, 166, 163, 0.15)" if is_dark else "#FFFFFF"

        self.setStyleSheet(f"""
            QFrame#CalendarDayCell {{
                background-color: {bg};
                border: {border_width}px solid {border_color};
                border-radius: 12px;
            }}
            QFrame#CalendarDayCell:hover {{
                border-color: {c.PRIMARY};
                background-color: {hover_bg};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.day_clicked.emit(self._jalali_date)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self._is_selected = selected
        self._apply_style()
        # به‌روزرسانی استایل شماره روز
        for child in self.findChildren(QLabel):
            if child.text().isdigit() and len(child.text()) <= 2:
                child.setStyleSheet(self._day_number_style())
                break