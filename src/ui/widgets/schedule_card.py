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
        self.setMinimumHeight(120)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(20)

        # ============================================
        # ۱. جعبه‌ی روز (راست‌ترین در RTL)
        # ============================================
        day_box = QFrame()
        day_box.setObjectName("AssignmentTimeBox")
        day_box.setFixedSize(100, 80)

        day_layout = QVBoxLayout(day_box)
        day_layout.setAlignment(Qt.AlignCenter)
        day_layout.setSpacing(4)
        day_layout.setContentsMargins(5, 5, 5, 5)

        icon = QLabel("📅")
        icon.setStyleSheet("font-size: 18pt; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(icon)

        day_label = QLabel(self._session.weekday or "—")
        day_label.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; color: {c.PRIMARY}; "
            "background: transparent;"
        )
        day_label.setAlignment(Qt.AlignCenter)
        day_layout.addWidget(day_label)

        layout.addWidget(day_box)

        # ============================================
        # ۲. اطلاعات (وسط) — هر ردیف با QLabel آیکون جدا
        # ============================================
        content_col = QVBoxLayout()
        content_col.setSpacing(8)
        content_col.setAlignment(Qt.AlignVCenter)

        # === ساعت ===
        time_text = self._session.time_range or "—"
        time_label = QLabel(f"⏰  {time_text}")
        time_label.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; color: {c.TEXT_PRIMARY}; "
            "background: transparent;"
        )
        time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        content_col.addWidget(time_label)

        # === مکان ===
        if self._session.location:
            location_label = QLabel(f"📍  {self._session.location}")
            location_label.setStyleSheet(
                f"font-size: 10pt; color: {c.TEXT_SECONDARY}; "
                "background: transparent;"
            )
            location_label.setWordWrap(True)
            location_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            content_col.addWidget(location_label)

        layout.addLayout(content_col, stretch=1)