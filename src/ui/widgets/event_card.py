"""Event Card: کارت نمایش یک رویداد — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.event import Event, EventType
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class EventCard(RTLWidgetMixin, QFrame):
    """کارت رویداد با نوار زمانی گرادیانتی و پیل نوع."""

    join_clicked = Signal(str)

    TYPE_META = {
        EventType.LIVE_SESSION: ("🎥", "جلسه آنلاین", "#2AA6A3"),
        EventType.EXAM: ("📝", "آزمون", "#FF9500"),
        EventType.DEADLINE: ("⏰", "مهلت", "#FF3B30"),
    }

    def __init__(self, event_data: Event, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._event_data = event_data
        self.setObjectName("EventCard")
        self.setMinimumHeight(110)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(16)

        # --- باکس زمان با گرادینت ---
        time_box = QFrame()
        time_box.setFixedSize(84, 84)
        time_box.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {_c('PRIMARY', '#2AA6A3')},
                    stop:1 {_c('PRIMARY_DARK', '#1E807E')});
                border-radius: 16px;
            }}
        """)
        time_lay = QVBoxLayout(time_box)
        time_lay.setAlignment(Qt.AlignCenter)
        time_lay.setSpacing(2)

        time_str = self._event_data.start_at.strftime("%H:%M") if self._event_data.start_at else "—"
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("color: #FFFFFF; font-size: 16pt; font-weight: 800; background: transparent;")
        time_lbl.setAlignment(Qt.AlignCenter)
        time_lay.addWidget(time_lbl)

        date_lbl = QLabel("زمان شروع")
        date_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 7.5pt; background: transparent;")
        date_lbl.setAlignment(Qt.AlignCenter)
        time_lay.addWidget(date_lbl)
        lay.addWidget(time_box)

        # --- محتوا ---
        content = QVBoxLayout()
        content.setSpacing(8)

        title = QLabel(self._event_data.title)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 12pt; "
            "font-weight: 700; background: transparent;"
        )
        content.addWidget(title)

        # پیل نوع
        icon_text, type_text, color = self.TYPE_META.get(
            self._event_data.event_type, ("📌", "رویداد", _c("TEXT_SECONDARY", "#3A3A3C"))
        )
        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)

        type_pill = QLabel(f"{icon_text}  {type_text}")
        type_pill.setFixedHeight(26)
        type_pill.setStyleSheet(
            f"color: {color}; background-color: {color}22; "
            "border-radius: 13px; padding: 0 12px; font-size: 8.5pt; font-weight: 700;"
        )
        badge_row.addWidget(type_pill)

        # مدت زمان (اگر end_at داشت)
        if self._event_data.start_at and self._event_data.end_at:
            delta = self._event_data.end_at - self._event_data.start_at
            minutes = int(delta.total_seconds() // 60)
            if minutes > 0:
                duration_pill = QLabel(f"⏱  {minutes} دقیقه")
                duration_pill.setFixedHeight(26)
                duration_pill.setStyleSheet(
                    f"color: {_c('TEXT_MUTED', '#8E8E93')}; "
                    f"background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.05)')}; "
                    "border-radius: 13px; padding: 0 12px; font-size: 8.5pt; font-weight: 600;"
                )
                badge_row.addWidget(duration_pill)

        badge_row.addStretch()
        content.addLayout(badge_row)
        lay.addLayout(content, stretch=1)

        # --- دکمه ورود ---
        join_btn = QPushButton("ورود به جلسه  ←")
        join_btn.setObjectName("PrimaryButton")
        join_btn.setMinimumWidth(140)
        join_btn.setFixedHeight(40)
        join_btn.setCursor(Qt.PointingHandCursor)
        join_btn.clicked.connect(self._on_join)
        lay.addWidget(join_btn)

    def _on_join(self) -> None:
        if self._event_data.url:
            QDesktopServices.openUrl(QUrl(self._event_data.url))
        self.join_clicked.emit(self._event_data.id)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._build()