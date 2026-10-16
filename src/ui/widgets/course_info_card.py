"""Course Info Card: کارت اطلاعات استاد — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.models.course import Course
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CourseInfoCard(RTLWidgetMixin, QFrame):
    """کارت اطلاعات درس (استاد با آواتار گرادیانتی)."""

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }

    def __init__(self, course: Course, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._course = course
        self.setObjectName("Card")
        self._build()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)
        lay.setDirection(QHBoxLayout.RightToLeft)

        # --- سربرگ ---
        head = QHBoxLayout()
        head.setSpacing(10)

        icon = QLabel("👨🏫")
        icon.setFixedSize(38, 38)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"background-color: {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')}; "
            "border-radius: 11px; font-size: 14pt;"
        )
        head.addWidget(icon)

        title = QLabel("استاد درس")
        title.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 10.5pt; "
            "font-weight: 600; background: transparent;"
        )
        head.addWidget(title, stretch=1)
        lay.addLayout(head)

        # --- آواتار + نام ---
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(14)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(64, 64)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self._set_initial_avatar()
        avatar_row.addWidget(self.avatar_label)

        info = QVBoxLayout()
        info.setSpacing(6)

        teacher_name = (self._course.teacher or "نامشخص").replace("استاد ", "").strip() or "نامشخص"
        name = QLabel(teacher_name)
        name.setWordWrap(True)
        name.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 800; "
            "font-size: 13.5pt; background: transparent;"
        )
        info.addWidget(name)

        # چیپ‌ها
        chips = QHBoxLayout()
        chips.setSpacing(8)
        if self._course.code:
            chips.addWidget(self._chip(f"📋 {self._course.code}"))
        _icon, domain_fa = self.DOMAIN_META.get(self._course.domain, ("⚪", self._course.domain))
        chips.addWidget(self._chip(f"{_icon} {domain_fa}"))
        chips.addStretch()
        info.addLayout(chips)

        avatar_row.addLayout(info, stretch=1)
        lay.addLayout(avatar_row)
        lay.addStretch()

    def _chip(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFixedHeight(26)
        lbl.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; "
            f"background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.05)')}; "
            "border-radius: 8px; padding: 0 10px; font-size: 8.5pt; font-weight: 600;"
        )
        return lbl

    def _set_initial_avatar(self) -> None:
        teacher_name = (self._course.teacher or "?").replace("استاد ", "").strip()
        initial = teacher_name[0] if teacher_name else "?"
        p = _c("PRIMARY", "#2AA6A3")
        pd = _c("PRIMARY_DARK", "#1E807E")
        self.avatar_label.setText(initial)
        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {p}, stop:1 {pd});
                color: #FFFFFF;
                border-radius: 32px;
                border: 3px solid {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.2)')};
                font-size: 24pt;
                font-weight: 800;
            }}
        """)