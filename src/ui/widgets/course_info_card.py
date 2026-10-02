"""Course Info Card: کارت اطلاعات استاد."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

from src.models.course import Course
from src.ui.theme import CurrentTheme


class CourseInfoCard(QFrame):
    """کارت اطلاعات درس (استاد با Avatar حرف اول)."""

    def __init__(self, course: Course, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._course = course
        self.setObjectName("Card")
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # === Header (آیکون + عنوان) ===
        header = QHBoxLayout()
        header.setSpacing(10)
        header.setDirection(QHBoxLayout.RightToLeft)

        title = QLabel("استاد درس")
        title.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 11pt; "
            "background: transparent; font-weight: 500;"
        )
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(title, stretch=1)

        icon = QLabel("👨‍🏫")
        icon.setStyleSheet("font-size: 16pt; background: transparent;")
        header.addWidget(icon)

        layout.addLayout(header)

        # === Avatar + Name Row ===
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(14)
        avatar_row.setDirection(QHBoxLayout.RightToLeft)

        # === Avatar ===
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(64, 64)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self._set_initial_avatar()

        avatar_row.addWidget(self.avatar_label)

        # === Name + Code ===
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        teacher_name = (self._course.teacher or "نامشخص").replace("استاد ", "").strip()

        name = QLabel(teacher_name)
        name.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
            "font-size: 14pt; background: transparent;"
        )
        name.setAlignment(Qt.AlignRight)
        name.setWordWrap(True)
        info_layout.addWidget(name)

        if self._course.code:
            code = QLabel(f"📋 کد درس: {self._course.code}")
            code.setStyleSheet(
                f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
                "background: transparent;"
            )
            code.setAlignment(Qt.AlignRight)
            info_layout.addWidget(code)

        avatar_row.addLayout(info_layout, stretch=1)
        layout.addLayout(avatar_row)

        layout.addStretch()

    def _set_initial_avatar(self) -> None:
        """Avatar با حرف اول نام."""
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        teacher_name = (self._course.teacher or "?").replace("استاد ", "").strip()
        initial = teacher_name[0] if teacher_name else "?"

        # رنگ پس‌زمینه‌ی دایره (آبی ملایم)
        if is_dark:
            bg_color = "rgba(96, 165, 250, 0.25)"
            text_color = c.PRIMARY
            border_color = "rgba(96, 165, 250, 0.5)"
        else:
            bg_color = "rgba(59, 130, 246, 0.15)"
            text_color = c.PRIMARY_DARK
            border_color = "rgba(59, 130, 246, 0.3)"

        self.avatar_label.setText(initial)
        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 32px;
                border: 2px solid {border_color};
                font-size: 26pt;
                font-weight: bold;
            }}
        """)