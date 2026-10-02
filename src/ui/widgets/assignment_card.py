"""Assignment Card: کارت نمایش یک تکلیف."""

from datetime import datetime

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

from src.models.assignment import Assignment
from src.ui.theme import Colors


class AssignmentCard(QFrame):
    """کارت نمایش یک تکلیف."""

    submit_clicked = Signal(str)  # assignment_id

    def __init__(self, assignment: Assignment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("AssignmentCard")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)

        # === Header (title) ===
        title = QLabel(self._assignment.title)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)

        # === Deadline Row ===
        deadline_row = QHBoxLayout()
        deadline_row.setSpacing(8)

        # وضعیت ددلاین
        deadline_icon, deadline_color, deadline_text = self._get_deadline_info()

        icon_label = QLabel(deadline_icon)
        icon_label.setStyleSheet("font-size: 12pt; background: transparent;")
        deadline_row.addWidget(icon_label)

        deadline_label = QLabel(deadline_text)
        deadline_label.setStyleSheet(
            f"color: {deadline_color}; font-weight: bold; "
            "background: transparent;"
        )
        deadline_label.setAlignment(Qt.AlignRight)
        deadline_row.addWidget(deadline_label, stretch=1)

        # تعداد پاسخ
        count_label = QLabel(f"👥  {self._assignment.response_count} پاسخ")
        count_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; background: transparent;"
        )
        deadline_row.addWidget(count_label)

        layout.addLayout(deadline_row)

        # === Actions ===
        actions = QHBoxLayout()
        actions.setSpacing(10)

        # دکمه ارسال پاسخ
        if self._assignment.submit_url:
            submit_btn = QPushButton("📤  ارسال پاسخ")
            submit_btn.setObjectName("PrimaryButton")
            submit_btn.setCursor(Qt.PointingHandCursor)
            submit_btn.clicked.connect(self._on_submit)
            actions.addWidget(submit_btn)

        # دکمه نظر استاد
        if self._assignment.view_url:
            view_btn = QPushButton("👁️  نظر استاد")
            view_btn.setObjectName("SecondaryButton")
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.clicked.connect(self._on_view)
            actions.addWidget(view_btn)

        actions.addStretch()
        layout.addLayout(actions)

    def _get_deadline_info(self) -> tuple[str, str, str]:
        """تشخیص وضعیت ددلاین."""
        if not self._assignment.deadline:
            return "⏰", Colors.TEXT_MUTED, "بدون ددلاین"

        now = datetime.now()
        deadline = self._assignment.deadline
        delta = deadline - now

        # ددلاین شمسی
        jalali = self._assignment.deadline_jalali or deadline.strftime("%Y-%m-%d %H:%M")

        if delta.total_seconds() < 0:
            return "⏹️", Colors.ERROR, f"گذشته — {jalali}"
        elif delta.days == 0:
            hours = delta.seconds // 3600
            return "🔥", Colors.ERROR, f"امروز! ({hours} ساعت مانده) — {jalali}"
        elif delta.days == 1:
            return "⚠️", Colors.WARNING, f"فردا — {jalali}"
        elif delta.days <= 3:
            return "⏰", Colors.WARNING, f"{delta.days} روز مانده — {jalali}"
        else:
            return "📅", Colors.SUCCESS, f"{delta.days} روز مانده — {jalali}"

    def _on_submit(self) -> None:
        if self._assignment.submit_url:
            QDesktopServices.openUrl(QUrl(self._assignment.submit_url))
        self.submit_clicked.emit(self._assignment.id)

    def _on_view(self) -> None:
        if self._assignment.view_url:
            QDesktopServices.openUrl(QUrl(self._assignment.view_url))