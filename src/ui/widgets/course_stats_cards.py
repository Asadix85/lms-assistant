"""Course Stats Cards: کارت‌های آمار درس."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    PostRepository,
)
from src.ui.theme import CurrentTheme


class CourseStatCard(QFrame):
    """یک کارت آماری برای درس."""

    def __init__(
        self,
        icon: str,
        label: str,
        value: str,
        extra: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(110)

        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 22pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {c.PRIMARY}; font-weight: bold; font-size: 18pt; "
            "background: transparent;"
        )
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)

        if extra:
            extra_widget = QLabel(extra)
            extra_widget.setStyleSheet(
                f"color: {c.TEXT_MUTED}; font-size: 8pt; "
                "background: transparent;"
            )
            extra_widget.setAlignment(Qt.AlignCenter)
            layout.addWidget(extra_widget)


class CourseStatsCards(QWidget):
    """ردیف کارت‌های آمار درس."""

    def __init__(
        self,
        db_path: str,
        course_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self._course_id = course_id
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()

    def _build(self) -> None:
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # === شمارش از دیتابیس ===
        try:
            with Database(self._db_path) as db:
                assignments = AssignmentRepository(db).get_by_course(self._course_id)
                contents = ContentRepository(db).get_by_course(self._course_id)
                posts = PostRepository(db).get_by_course(self._course_id, limit=1000)
        except Exception:
            assignments, contents, posts = [], [], []

        # === تکالیف ===
        assignment_count = len(assignments)
        # تعداد تکالیف نزدیک
        from datetime import datetime
        now = datetime.now()
        upcoming = sum(
            1 for a in assignments
            if a.deadline and a.deadline >= now
        )
        assignment_extra = f"{upcoming} فعال" if upcoming > 0 else ""

        # === فایل‌ها ===
        content_count = len(contents)
        # نوع فایل‌ها
        types = set(c.content_type for c in contents)
        content_extra = "، ".join(sorted(types)[:2]) if types else ""

        # === پیام‌ها ===
        post_count = len(posts)
        post_extra = ""

        # === ساخت کارت‌ها ===
        layout.addWidget(CourseStatCard(
            icon="📋",
            label="تکلیف",
            value=self._to_fa(assignment_count),
            extra=assignment_extra,
        ))

        layout.addWidget(CourseStatCard(
            icon="📄",
            label="فایل",
            value=self._to_fa(content_count),
            extra=content_extra,
        ))

        layout.addWidget(CourseStatCard(
            icon="📢",
            label="پیام",
            value=self._to_fa(post_count),
            extra=post_extra,
        ))

    @staticmethod
    def _to_fa(n: int) -> str:
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))