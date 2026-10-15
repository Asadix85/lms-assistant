"""Quera Course Card: کارت نمایش یک کلاس Quera — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.models.quera_course import QueraCourse
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class QueraCourseCard(QFrame):
    """کارت کلاس Quera — با هویت رنگی متمایز (Accent)."""

    clicked = Signal(str)

    def __init__(self, course: QueraCourse, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._course = course
        self.setObjectName("CourseCard")
        self.setMinimumHeight(210)
        self.setMinimumWidth(280)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        accent = _c("ACCENT", "#FF9500")
        accent_dark = _c("ACCENT_DARK", "#CC7700")
        accent_bg = "rgba(255, 149, 0, 0.12)"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        # --- سربرگ: آیکون + بج کوئرا ---
        head = QHBoxLayout()
        head.setSpacing(10)

        icon_lbl = QLabel("💻")
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {accent_bg}; border-radius: 12px; font-size: 15pt;"
        )
        head.addWidget(icon_lbl)
        head.addStretch()

        badge = QLabel("🎯 کوئرا")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedHeight(24)
        badge.setStyleSheet(
            f"color: {accent}; background-color: {accent_bg}; border-radius: 12px; "
            "padding: 0 12px; font-size: 8.5pt; font-weight: 700;"
        )
        head.addWidget(badge)
        lay.addLayout(head)

        # --- عنوان ---
        title = QLabel(self._course.name)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 12.5pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        # --- استاد ---
        if self._course.teacher:
            teacher = QLabel(f"👤  {self._course.teacher}")
            teacher.setStyleSheet(
                f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
            )
            lay.addWidget(teacher)

        lay.addStretch()

        # --- چیپ آمار ---
        stats = QLabel(f"📋  {self._course.assignments_count} تمرین")
        stats.setFixedHeight(26)
        stats.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; "
            f"background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.05)')}; "
            "border-radius: 8px; padding: 0 10px; font-size: 8.5pt;"
        )
        lay.addWidget(stats, alignment=Qt.AlignRight)

        # --- دکمه‌ی گرادیانتی ---
        btn = QPushButton("باز کردن در کوئرا  ↗")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(38)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent_dark});
                color: #FFFFFF; border: none; border-radius: 12px;
                padding: 8px 16px; font-size: 10pt; font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_dark}, stop:1 {accent_dark});
            }}
        """)
        btn.clicked.connect(self._on_open)
        lay.addWidget(btn)

    def _on_open(self) -> None:
        QDesktopServices.openUrl(QUrl(f"https://quera.org/course/{self._course.id}"))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not isinstance(child, QPushButton):
                self.clicked.emit(self._course.synthetic_id)
        super().mousePressEvent(event)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._build()