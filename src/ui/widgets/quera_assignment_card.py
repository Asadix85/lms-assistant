"""Quera Assignment Card: کارت نمایش یک تمرین Quera."""

from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from src.models.quera_assignment import QueraAssignment
from src.ui.theme import CurrentTheme


class QueraAssignmentCard(QFrame):
    """کارت تمرین Quera."""

    def __init__(
        self,
        assignment: QueraAssignment,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("AssignmentCard")
        self.setMinimumHeight(110)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(15)

        # === Time Box ===
        time_box = QFrame()
        time_box.setObjectName("AssignmentTimeBox")
        time_box.setFixedSize(80, 80)

        time_layout = QVBoxLayout(time_box)
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.setSpacing(2)

        icon = QLabel("🎯")
        icon.setStyleSheet("font-size: 14pt; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(icon)

        # روز مانده
        days = self._assignment.days_left
        if days < 0:
            time_text = "گذشت"
            color = c.TEXT_MUTED
        elif days == 0:
            time_text = "امروز"
            color = c.ERROR
        elif days == 1:
            time_text = "۱ روز"
            color = c.WARNING
        else:
            time_text = self._to_fa(days) + " روز"
            color = c.PRIMARY if days > 3 else c.WARNING

        time_label = QLabel(time_text)
        time_label.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; color: {color}; "
            "background: transparent;"
        )
        time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(time_label)

        layout.addWidget(time_box)

        # === Content ===
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        # عنوان
        title = QLabel(self._assignment.name)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight)
        content_layout.addWidget(title)

        # نام درس + badge
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        course = QLabel(f"📚  {self._assignment.course_name}")
        course.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        course.setAlignment(Qt.AlignRight)
        meta_row.addWidget(course)

        # badge کوئرا
        badge = QLabel("🎯  کوئرا")
        badge.setStyleSheet(
            f"background-color: {c.PRIMARY}22; color: {c.PRIMARY}; "
            "padding: 3px 10px; border-radius: 10px; font-size: 9pt;"
        )
        meta_row.addWidget(badge)

        meta_row.addStretch()
        content_layout.addLayout(meta_row)

        # پیشرفت
        progress_text = (
            f"📊  {self._to_fa(self._assignment.submitted_count)} از "
            f"{self._to_fa(self._assignment.problems_count)} سؤال"
        )
        progress_label = QLabel(progress_text)
        progress_label.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; background: transparent;"
        )
        progress_label.setAlignment(Qt.AlignRight)
        content_layout.addWidget(progress_label)

        layout.addLayout(content_layout, stretch=1)

        # === Action ===
        open_btn = QPushButton("🚪  باز کردن")
        open_btn.setObjectName("PrimaryButton")
        open_btn.setMinimumWidth(120)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self._on_open)
        layout.addWidget(open_btn)

    def _on_open(self) -> None:
        url = (
            f"https://quera.org/course/assignments/"
            f"{self._assignment.id}/problems"
        )
        QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _to_fa(n: int) -> str:
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))