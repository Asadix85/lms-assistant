"""Quera Course Card: کارت نمایش یک کلاس Quera."""

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

from src.models.quera_course import QueraCourse
from src.ui.theme import CurrentTheme


class QueraCourseCard(QFrame):
    """کارت کلاس Quera."""

    clicked = Signal(str)  # course_id

    def __init__(
        self,
        course: QueraCourse,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._course = course
        self.setObjectName("CourseCard")
        self.setMinimumHeight(200)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)

        # === Header: badge + title ===
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        # badge کوئرا
        badge = QLabel("🎯  کوئرا")
        badge.setStyleSheet(
            f"background-color: {c.PRIMARY}22; color: {c.PRIMARY}; "
            "padding: 3px 10px; border-radius: 10px; font-size: 9pt;"
        )
        header_row.addWidget(badge)

        header_row.addStretch()

        # آیکون
        icon = QLabel("💻")
        icon.setStyleSheet("font-size: 18pt; background: transparent;")
        header_row.addWidget(icon)

        layout.addLayout(header_row)

        # === Title ===
        title = QLabel(self._course.name)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight)
        title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent;"
        )
        layout.addWidget(title)

        # === Teacher ===
        if self._course.teacher:
            teacher = QLabel(f"👤  {self._course.teacher}")
            teacher.setStyleSheet(
                f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
                "background: transparent;"
            )
            teacher.setAlignment(Qt.AlignRight)
            layout.addWidget(teacher)

        layout.addStretch()

        # === Stats ===
        stats_text = f"📋  {self._course.assignments_count} تمرین"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 10pt; "
            "background: transparent;"
        )
        stats_label.setAlignment(Qt.AlignRight)
        layout.addWidget(stats_label)

        # === Button ===
        open_btn = QPushButton("🎯  باز کردن در کوئرا")
        open_btn.setObjectName("PrimaryButton")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setMinimumHeight(38)
        open_btn.clicked.connect(self._on_open)
        layout.addWidget(open_btn)

    def _on_open(self) -> None:
        url = f"https://quera.org/course/{self._course.id}"
        QDesktopServices.openUrl(QUrl(url))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._course.synthetic_id)
        super().mousePressEvent(event)