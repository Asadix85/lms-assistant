"""Schedule Card: کارت نمایش یک جلسه‌ی کلاس."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

from src.models.course_schedule import ClassSession
from src.ui.theme import CurrentTheme


class ScheduleCard(QFrame):
    """کارت نمایش یک جلسه‌ی کلاس."""

    def __init__(
        self,
        session: ClassSession,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session = session
        self.setObjectName("Card")
        self.setMinimumHeight(110)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # === آیکون روز (چپ) ===
        day_box = QFrame()
        day_box.setObjectName("AssignmentTimeBox")
        day_box.setFixedSize(90, 75)

        day_layout = QVBoxLayout(day_box)
        day_layout.setAlignment(Qt.AlignCenter)
        day_layout.setSpacing(2)

        icon = QLabel("📅")
        icon.setStyleSheet("font-size: 16pt; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(icon)

        day_label = QLabel(self._session.weekday or "—")
        day_label.setStyleSheet(
            f"font-size: 11pt; font-weight: bold; color: {c.PRIMARY}; "
            "background: transparent;"
        )
        day_label.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(day_label)

        layout.addWidget(day_box)

        # === اطلاعات (وسط) ===
        content_col = QVBoxLayout()
        content_col.setSpacing(10)
        content_col.setAlignment(Qt.AlignVCenter)

        # ساعت
        time_text = self._session.time_range or "—"
        time_row = QHBoxLayout()
        time_row.setSpacing(8)

        time_icon = QLabel("⏰")
        time_icon.setStyleSheet("font-size: 12pt; background: transparent;")
        time_row.addWidget(time_icon)

        time_label = QLabel(time_text)
        time_label.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; color: {c.TEXT_PRIMARY}; "
            "background: transparent;"
        )
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_row.addWidget(time_label, stretch=1)

        content_col.addLayout(time_row)

        # مکان
        if self._session.location:
            location_row = QHBoxLayout()
            location_row.setSpacing(8)

            loc_icon = QLabel("📍")
            loc_icon.setStyleSheet("font-size: 12pt; background: transparent;")
            loc_icon.setAlignment(Qt.AlignTop)
            location_row.addWidget(loc_icon)

            location_label = QLabel(self._session.location)
            location_label.setStyleSheet(
                f"font-size: 10pt; color: {c.TEXT_SECONDARY}; "
                "background: transparent;"
            )
            location_label.setWordWrap(True)
            location_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            location_row.addWidget(location_label, stretch=1)

            content_col.addLayout(location_row)

        layout.addLayout(content_col, stretch=1)