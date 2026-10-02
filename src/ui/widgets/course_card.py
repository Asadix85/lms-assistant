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

    clicked = Signal(str)  # course_id

    DOMAIN_META = {
        "lms3": ("🟢", Colors.LMS3, "علوم پایه"),
        "lms4": ("🔵", Colors.LMS4, "فنی-مهندسی"),
        "lms5": ("🔴", Colors.LMS5, "اداری-تربیتی"),
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
        icon, color, _ = self.DOMAIN_META.get(
            self.course.domain, ("⚪", Colors.TEXT_MUTED, "نامشخص")
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # === Title Row ===
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        domain_icon = QLabel(icon)
        domain_icon.setStyleSheet("font-size: 16pt;")
        title_row.addWidget(domain_icon)

        title = QLabel(self.course.name)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title_row.addWidget(title, stretch=1)

        layout.addLayout(title_row)

        # === Status badge ===
        if self.course.status == CourseStatus.FINISHED:
            badge = QLabel("⏹ پایان یافته")
            badge.setStyleSheet(
                "background-color: #F0F2F5; color: #7F8C8D; "
                "padding: 3px 8px; border-radius: 4px; font-size: 8pt;"
            )
            badge.setAlignment(Qt.AlignRight)
            layout.addWidget(badge)

        # === Teacher ===
        teacher = QLabel(f"👨‍🏫  {self.course.teacher or '—'}")
        teacher.setObjectName("CardSubtitle")
        layout.addWidget(teacher)

        # === Code ===
        code_text = self.course.code or "—"
        code = QLabel(f"📋  کد: {code_text}")
        code.setObjectName("CardSubtitle")
        layout.addWidget(code)

        layout.addStretch()

        # === Action button ===
        btn = QPushButton("مشاهده جزئیات")
        btn.setObjectName("SecondaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.clicked.emit(self.course.id))
        layout.addWidget(btn)

    def enterEvent(self, event) -> None:
        """Hover."""
        self.setStyleSheet(f"""
            QFrame#CourseCard {{
                background-color: white;
                border: 2px solid {Colors.PRIMARY};
                border-radius: 12px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """خروج از hover."""
        self.setStyleSheet("")
        super().leaveEvent(event)