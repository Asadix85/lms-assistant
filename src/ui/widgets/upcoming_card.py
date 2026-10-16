"""Upcoming Card: کارت رویداد/مهلت نزدیک — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.models.assignment import Assignment
from src.models.event import Event
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin, mark_ltr


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class UpcomingCard(RTLWidgetMixin, QFrame):
    """کارت رویداد/مهلت با نوار رنگی وضعیت."""

    clicked = Signal(str)

    def __init__(
        self,
        item: Event | Assignment,
        item_type: str,
        course_name: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._item = item
        self._item_type = item_type
        self._course_name = course_name
        self._course_id = getattr(item, 'course_id', '') or ''
        self.setObjectName("UpcomingCard")
        self.setFixedHeight(76)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # --- نوار رنگی سمت راست ---
        status_color = self._get_status_color()
        color_bar = QFrame()
        color_bar.setFixedWidth(5)
        color_bar.setStyleSheet(f"background-color: {status_color}; border-top-left-radius: 12px; border-bottom-left-radius: 12px;")
        lay.addWidget(color_bar)

        # --- محتوا ---
        content = QWidget()
        content_lay = QHBoxLayout(content)
        content_lay.setContentsMargins(14, 10, 14, 10)
        content_lay.setSpacing(12)

        # آیکون
        icon_text = "🎥" if self._item_type == "event" else "📋"
        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 16pt; background: transparent;")
        icon.setFixedWidth(28)
        content_lay.addWidget(icon)

        # متن
        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        # عنوان + بج
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title = QLabel(getattr(self._item, 'title', ''))
        title.setStyleSheet(f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 700; font-size: 10.5pt; background: transparent;")
        title_row.addWidget(title, stretch=1)

        from src.utils.quera_adapter import is_quera_item
        if is_quera_item(self._item):
            badge = QLabel("🎯 کوئرا")
            badge.setFixedHeight(20)
            badge.setStyleSheet(f"color: {_c('ACCENT', '#FF9500')}; background-color: {_c('ACCENT', '#FF9500')}22; border-radius: 10px; padding: 0 8px; font-size: 7.5pt; font-weight: 700;")
            title_row.addWidget(badge)
        text_col.addLayout(title_row)

        # نام درس
        if self._course_name:
            course_lbl = QLabel(self._course_name)
            course_lbl.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;")
            text_col.addWidget(course_lbl)
        content_lay.addLayout(text_col, stretch=1)

        # زمان
        time_text, _ = self._get_time_info()
        time_lbl = QLabel(time_text)
        time_lbl.setStyleSheet(f"color: {status_color}; font-weight: 800; font-size: 10pt; background: transparent;")
        time_lbl.setMinimumWidth(80)
        # ساعت/تاریخ لاتین عمداً LTR: "14:30" نباید معکوس نمایش داده شود
        mark_ltr(time_lbl)
        time_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        content_lay.addWidget(time_lbl)

        lay.addWidget(content, stretch=1)

        # افکت hover بر اساس تم
        is_dark = CurrentTheme.is_dark()
        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        self.setStyleSheet(f"""
            QFrame#UpcomingCard {{
                background-color: {card_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 12px;
            }}
            QFrame#UpcomingCard:hover {{
                background-color: {card_hover};
                border-color: {status_color}50;
            }}
        """)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        status_color = self._get_status_color()
        is_dark = CurrentTheme.is_dark()

        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        self.setStyleSheet(f"""
            QFrame#UpcomingCard {{
                background-color: {card_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 12px;
            }}
            QFrame#UpcomingCard:hover {{
                background-color: {card_hover};
                border-color: {status_color}50;
            }}
        """)

        # به‌روزرسانی نوار رنگی
        for child in self.findChildren(QFrame):
            if child.width() == 5:  # نوار رنگی
                child.setStyleSheet(
                    f"background-color: {status_color}; border-top-left-radius: 12px; border-bottom-left-radius: 12px;")
                break

    def _get_status_color(self) -> str:
        time_text, color = self._get_time_info()
        return color

    def _get_time_info(self) -> tuple[str, str]:
        if self._item_type == "event":
            return self._get_event_time()
        else:
            return self._get_assignment_time()

    def _get_event_time(self) -> tuple[str, str]:
        if not hasattr(self._item, 'start_at') or not self._item.start_at:
            return "—", _c('TEXT_MUTED', '#8E8E93')

        delta = self._item.start_at - datetime.now()
        seconds = delta.total_seconds()

        if seconds < 0:
            return "گذشته", _c('TEXT_MUTED', '#8E8E93')
        elif seconds < 3600:
            return f"{int(seconds / 60)} دقیقه", _c('ERROR', '#FF3B30')
        elif seconds < 86400:
            return f"{int(seconds / 3600)} ساعت", _c('WARNING', '#FF9500')
        else:
            return f"{int(seconds / 86400)} روز", _c('PRIMARY', '#2AA6A3')

    def _get_assignment_time(self) -> tuple[str, str]:
        if not hasattr(self._item, 'deadline') or not self._item.deadline:
            return "—", _c('TEXT_MUTED', '#8E8E93')

        delta = self._item.deadline - datetime.now()
        seconds = delta.total_seconds()

        if seconds < 0:
            return "گذشته", _c('ERROR', '#FF3B30')
        elif seconds < 86400:
            return f"{int(seconds / 3600)} ساعت", _c('ERROR', '#FF3B30')
        elif seconds < 3 * 86400:
            return f"{int(seconds / 86400)} روز", _c('WARNING', '#FF9500')
        else:
            return f"{int(seconds / 86400)} روز", _c('SUCCESS', '#34C759')

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._course_id)
        super().mousePressEvent(event)