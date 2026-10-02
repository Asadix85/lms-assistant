"""Event Card: کارت نمایش یک رویداد (جلسه آنلاین)."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices

from src.models.event import Event, EventType
from src.ui.theme import Colors


class EventCard(QFrame):
    """کارت رویداد (جلسه آنلاین)."""

    join_clicked = Signal(str)  # event_id

    def __init__(self, event_data: Event, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # ⚠️ اسم attribute رو از self.event به self._event_data عوض کردیم
        self._event_data = event_data
        self.setObjectName("EventCard")
        self.setMinimumHeight(100)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(15)

        # === Time Box (Left) ===
        time_box = QFrame()
        time_box.setObjectName("TimeBox")
        time_box.setFixedSize(80, 70)

        time_layout = QVBoxLayout(time_box)
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.setSpacing(2)

        icon = QLabel("🕐")
        icon.setStyleSheet("font-size: 14pt; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(icon)

        time_str = (
            self._event_data.start_at.strftime("%H:%M")
            if self._event_data.start_at
            else "—"
        )
        time_label = QLabel(time_str)
        time_label.setStyleSheet(
            f"font-size: 14pt; font-weight: bold; color: {Colors.PRIMARY}; "
            "background: transparent;"
        )
        time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(time_label)

        layout.addWidget(time_box)

        # === Content (Middle) ===
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        title = QLabel(self._event_data.title)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight)
        content_layout.addWidget(title)

        # Event type badge
        type_meta = {
            EventType.LIVE_SESSION: ("🎥", "جلسه آنلاین", Colors.PRIMARY),
            EventType.EXAM: ("📝", "آزمون", Colors.WARNING),
            EventType.DEADLINE: ("⏰", "مهلت", Colors.ERROR),
        }
        icon_text, type_text, color = type_meta.get(
            self._event_data.event_type,
            ("📌", "رویداد", Colors.TEXT_SECONDARY),
        )

        badge = QLabel(f"{icon_text}  {type_text}")
        badge.setStyleSheet(
            f"background-color: {color}22; color: {color}; "
            "padding: 3px 10px; border-radius: 10px; font-size: 9pt;"
        )
        badge.setAlignment(Qt.AlignRight)
        badge.setMaximumWidth(150)
        content_layout.addWidget(badge)

        layout.addLayout(content_layout, stretch=1)

        # === Action (Right) ===
        self.join_btn = QPushButton("🚪  ورود به جلسه")
        self.join_btn.setObjectName("PrimaryButton")
        self.join_btn.setMinimumWidth(140)
        self.join_btn.setCursor(Qt.PointingHandCursor)
        self.join_btn.clicked.connect(self._on_join)
        layout.addWidget(self.join_btn)

    def _on_join(self) -> None:
        """کلیک روی ورود."""
        if self._event_data.url:
            QDesktopServices.openUrl(QUrl(self._event_data.url))
        self.join_clicked.emit(self._event_data.id)