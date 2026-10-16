"""Assignment Card: کارت نمایش یک تکلیف — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from datetime import datetime

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

from src.models.assignment import Assignment
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class AssignmentCard(RTLWidgetMixin, QFrame):
    """کارت نمایش یک تکلیف با نوار زمانی و پیل وضعیت."""

    submit_clicked = Signal(str)

    def __init__(self, assignment: Assignment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("AssignmentCard")
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        # --- عنوان + پیل وضعیت ---
        head = QHBoxLayout()
        head.setSpacing(10)

        title = QLabel(self._assignment.title)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 12pt; "
            "font-weight: 700; background: transparent;"
        )
        head.addWidget(title, stretch=1)

        deadline_icon, deadline_color, deadline_text = self._get_deadline_info()
        pill = QLabel(deadline_text)
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedHeight(26)
        pill.setStyleSheet(
            f"color: {deadline_color}; background-color: {deadline_color}22; "
            "border-radius: 13px; padding: 0 12px; font-size: 8.5pt; font-weight: 700;"
        )
        head.addWidget(pill)
        lay.addLayout(head)

        # --- نوار زمانی ---
        time_box = QFrame()
        time_box.setObjectName("AssignmentTimeBox")
        time_lay = QVBoxLayout(time_box)
        time_lay.setContentsMargins(14, 12, 14, 12)
        time_lay.setSpacing(8)

        start_text = self._assignment.start_at_jalali or self._format_dt(self._assignment.start_at)
        if start_text:
            time_lay.addWidget(self._time_row("▶️", "شروع:", start_text, _c("SUCCESS", "#34C759")))

        end_text = self._assignment.deadline_jalali or self._format_dt(self._assignment.deadline)
        if end_text:
            time_lay.addWidget(self._time_row("⏹️", "پایان:", end_text, _c("ERROR", "#FF3B30")))

        lay.addWidget(time_box)

        # --- دکمه‌ها ---
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        if self._assignment.submit_url:
            btn = QPushButton("📤  ارسال پاسخ")
            btn.setObjectName("PrimaryButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(self._on_submit)
            actions.addWidget(btn)

        if self._assignment.view_url:
            btn = QPushButton("👁️  نظر استاد")
            btn.setObjectName("SecondaryButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(self._on_view)
            actions.addWidget(btn)

        lay.addLayout(actions)

    def _time_row(self, icon: str, label: str, value: str, color: str) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 10pt; background: transparent;")
        ic.setFixedWidth(20)
        row.addWidget(ic)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
        )
        lbl.setFixedWidth(50)
        row.addWidget(lbl)

        val = QLabel(value)
        val.setStyleSheet(
            f"color: {color}; font-size: 9.5pt; font-weight: 700; background: transparent;"
        )
        row.addWidget(val, stretch=1)
        return w

    def _get_deadline_info(self):
        if not self._assignment.deadline:
            return "⏰", _c("TEXT_MUTED", "#8E8E93"), "بدون ددلاین"

        now = datetime.now()
        delta = self._assignment.deadline - now

        if delta.total_seconds() < 0:
            return "⏹️", _c("TEXT_MUTED", "#8E8E93"), "مهلت گذشته"
        elif delta.days == 0:
            hours = delta.seconds // 3600
            return "🔥", _c("ERROR", "#FF3B30"), f"امروز! {hours} ساعت مانده"
        elif delta.days == 1:
            return "⚠️", _c("ACCENT", "#FF9500"), "فردا!"
        elif delta.days <= 3:
            return "⏰", _c("WARNING", "#FF9500"), f"{delta.days} روز مانده"
        else:
            return "📅", _c("SUCCESS", "#34C759"), f"{delta.days} روز مانده"

    @staticmethod
    def _format_dt(dt) -> str:
        return dt.strftime("%Y-%m-%d %H:%M") if dt else ""

    def _on_submit(self) -> None:
        if self._assignment.submit_url:
            QDesktopServices.openUrl(QUrl(self._assignment.submit_url))
        self.submit_clicked.emit(self._assignment.id)

    def _on_view(self) -> None:
        if self._assignment.view_url:
            QDesktopServices.openUrl(QUrl(self._assignment.view_url))

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._build()