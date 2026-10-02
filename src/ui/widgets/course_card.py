"""Course Card: کارت نمایش یک درس."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from src.models.course import Course, CourseStatus
from src.ui.theme import Colors


class CourseCard(QFrame):
    """کارت نمایش یک درس."""

    clicked = Signal(str)

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }

    def __init__(self, course: Course, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.course = course
        self.setObjectName("CourseCard")
        self.setFixedHeight(200)
        self.setMinimumWidth(280)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        # ⚠️ فقط ۲ تا unpack
        icon, _ = self.DOMAIN_META.get(self.course.domain, ("⚪", "نامشخص"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # Title Row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        domain_icon = QLabel(icon)
        domain_icon.setStyleSheet("font-size: 16pt; background: transparent;")
        title_row.addWidget(domain_icon)

        title = QLabel(self.course.name)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight | Qt.AlignTop)
        title_row.addWidget(title, stretch=1)

        layout.addLayout(title_row)

        # Status badge
        if self.course.status == CourseStatus.FINISHED:
            badge = QLabel("⏹ پایان یافته")
            badge.setStyleSheet(
                "background-color: rgba(148, 163, 184, 0.2); "
                "color: #64748B; padding: 3px 8px; border-radius: 6px; "
                "font-size: 8pt;"
            )
            badge.setAlignment(Qt.AlignRight)
            layout.addWidget(badge)

        # Teacher
        teacher = QLabel(f"👨‍🏫  {self.course.teacher or '—'}")
        teacher.setObjectName("CardSubtitle")
        layout.addWidget(teacher)

        # Code
        code_text = self.course.code or "—"
        code = QLabel(f"📋  کد: {code_text}")
        code.setObjectName("CardSubtitle")
        layout.addWidget(code)

        layout.addStretch()

        # Action button
        btn = QPushButton("مشاهده جزئیات")
        btn.setObjectName("SecondaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.clicked.emit(self.course.id))
        layout.addWidget(btn)

    def mousePressEvent(self, event) -> None:
        """کلیک روی کارت → انتخاب."""
        self.clicked.emit(self.course.id)
        super().mousePressEvent(event)