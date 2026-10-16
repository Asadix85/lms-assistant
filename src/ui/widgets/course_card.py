"""Course Card: کارت نمایش یک درس — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.models.course import Course, CourseStatus
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CourseCard(RTLWidgetMixin, QFrame):
    """کارت نمایش یک درس LMS."""

    clicked = Signal(str)

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }
    DOMAIN_COLOR = {
        "lms3": ("#34C759", "rgba(52, 199, 89, 0.14)"),
        "lms4": ("#2AA6A3", "rgba(42, 166, 163, 0.14)"),
        "lms5": ("#FF3B30", "rgba(255, 59, 48, 0.12)"),
    }

    def __init__(self, course: Course, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.course = course
        self.setObjectName("CourseCard")
        self.setMinimumHeight(210)
        self.setMinimumWidth(280)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        icon, _fa = self.DOMAIN_META.get(self.course.domain, ("⚪", "نامشخص"))
        _fg, icon_bg = self.DOMAIN_COLOR.get(
            self.course.domain,
            (_c("PRIMARY", "#2AA6A3"), _c("PRIMARY_LIGHT", "rgba(42,166,163,0.14)")),
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        # --- سربرگ: آیکون دامنه + پیل وضعیت ---
        head = QHBoxLayout()
        head.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(42, 42)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {icon_bg}; border-radius: 12px; "
            "font-size: 15pt; background-clip: padding-box;"
        )
        head.addWidget(icon_lbl)
        head.addStretch()

        if self.course.status == CourseStatus.FINISHED:
            p_txt, p_fg, p_bg = "پایان‌یافته", _c("TEXT_MUTED", "#8E8E93"), _c("BG_HOVER", "rgba(148,163,184,0.15)")
        else:
            p_txt, p_fg, p_bg = "فعال", _c("SUCCESS", "#34C759"), "rgba(52, 199, 89, 0.12)"
        pill = QLabel(p_txt)
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedHeight(24)
        pill.setStyleSheet(
            f"color: {p_fg}; background-color: {p_bg}; border-radius: 12px; "
            "padding: 0 12px; font-size: 8.5pt; font-weight: 700;"
        )
        head.addWidget(pill)
        lay.addLayout(head)

        # --- عنوان ---
        title = QLabel(self.course.name)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 12.5pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        # --- استاد با آواتار حرف اول ---
        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        t_name = (self.course.teacher or "").replace("استاد ", "").strip() or "نامشخص"

        avatar = QLabel(t_name[0])
        avatar.setFixedSize(26, 26)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"background-color: {_c('BG_HOVER', 'rgba(0,0,0,0.06)')}; "
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; border-radius: 13px; "
            "font-size: 10pt; font-weight: 700;"
        )
        t_row.addWidget(avatar)

        t_lbl = QLabel(t_name)
        t_lbl.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
        )
        t_row.addWidget(t_lbl)
        t_row.addStretch()
        lay.addLayout(t_row)

        lay.addStretch()

        # --- پابرنگ: چیپ کد + دکمه مشاهده ---
        foot = QHBoxLayout()
        foot.setSpacing(10)

        code = QLabel(f"کد: {self.course.code or '—'}")
        code.setFixedHeight(26)
        code.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; "
            f"background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.05)')}; "
            "border-radius: 8px; padding: 0 10px; font-size: 8.5pt;"
        )
        foot.addWidget(code)
        foot.addStretch()

        btn = QPushButton("مشاهده  ←")
        btn.setObjectName("SecondaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(34)
        btn.clicked.connect(lambda: self.clicked.emit(self.course.id))
        foot.addWidget(btn)
        lay.addLayout(foot)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not isinstance(child, QPushButton):  # جلوگیری از double emit
                self.clicked.emit(self.course.id)
        super().mousePressEvent(event)