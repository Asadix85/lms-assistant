"""Course Detail Page: صفحه‌ی جزئیات یک درس."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal

from src.models.course import Course
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    PostRepository,
)
from src.ui.theme import Colors
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.course_card import CourseCard  # برای domain icon
from src.ui.widgets.post_card import PostCard


class CourseDetailPage(QWidget):
    """صفحه‌ی جزئیات یک درس."""

    back_clicked = Signal()

    DOMAIN_META = {
        "lms3": ("🟢", "علوم پایه"),
        "lms4": ("🔵", "فنی-مهندسی"),
        "lms5": ("🔴", "اداری-تربیتی"),
    }

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_path = db_path
        self._course: Course | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # === Header Row ===
        header = QHBoxLayout()

        back_btn = QPushButton("←  بازگشت به دروس")
        back_btn.setObjectName("SecondaryButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(back_btn)

        header.addStretch()

        layout.addLayout(header)

        # === Course Info ===
        self.info_container = QFrame()
        self.info_container.setObjectName("CourseInfoHeader")
        info_layout = QVBoxLayout(self.info_container)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(8)

        self.course_title = QLabel("—")
        self.course_title.setObjectName("PageTitle")
        self.course_title.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.course_title)

        self.course_meta = QLabel("—")
        self.course_meta.setObjectName("PageSubtitle")
        self.course_meta.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self.course_meta)

        layout.addWidget(self.info_container)

        # === Tabs (پیام‌ها، تکالیف، فایل‌ها) ===
        self.tabs = QTabWidget()

        # Tab 1: Posts
        self.posts_container = self._build_tab_container()
        self.tabs.addTab(self.posts_container, "📢 پیام‌ها")

        # Tab 2: Assignments
        self.assignments_container = self._build_tab_container()
        self.tabs.addTab(self.assignments_container, "📋 تکالیف")

        # Tab 3: Contents
        self.contents_container = self._build_tab_container()
        self.tabs.addTab(self.contents_container, "📄 فایل‌ها")

        layout.addWidget(self.tabs, stretch=1)

    def _build_tab_container(self) -> QScrollArea:
        """ساخت یک QScrollArea با QVBoxLayout برای tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setAlignment(Qt.AlignTop)
        widget.setLayout(layout)

        scroll.setWidget(widget)

        # ذخیره‌ی layout برای دسترسی
        scroll._content_layout = layout
        return scroll

    def _clear_layout(self, layout) -> None:
        """پاک کردن همه widgetها."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # === Data ===

    def load_course(self, course: Course) -> None:
        """بارگذاری اطلاعات یک درس."""
        self._course = course

        # Header
        icon, _ = self.DOMAIN_META.get(course.domain, ("⚪", "?"))
        self.course_title.setText(f"{icon}  {course.name}")

        meta_parts = []
        if course.teacher:
            meta_parts.append(f"👨‍🏫 {course.teacher}")
        if course.code:
            meta_parts.append(f"📋 {course.code}")
        meta_parts.append(f"🌐 {course.domain}")
        self.course_meta.setText("  •  ".join(meta_parts))

        # Load tabs
        self._load_posts()
        self._load_assignments()
        self._load_contents()

        # برو به تب پیام‌ها
        self.tabs.setCurrentIndex(0)

    def _load_posts(self) -> None:
        """بارگذاری پیام‌ها."""
        if not self._course:
            return

        layout = self.posts_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = PostRepository(db)
                posts = repo.get_by_course(self._course.group_id, limit=50)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not posts:
            empty = QLabel("📭  هنوز پیامی در این درس نیست.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return

        for p in posts:
            card = PostCard(p)
            layout.addWidget(card)

        # آپدیت عنوان tab
        self.tabs.setTabText(0, f"📢 پیام‌ها ({len(posts)})")

    def _load_assignments(self) -> None:
        """بارگذاری تکالیف."""
        if not self._course:
            return

        layout = self.assignments_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = AssignmentRepository(db)
                assignments = repo.get_by_course(self._course.group_id)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not assignments:
            empty = QLabel("📭  هنوز تکلیفی در این درس نیست.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return

        for a in assignments:
            card = AssignmentCard(a)
            layout.addWidget(card)

        self.tabs.setTabText(1, f"📋 تکالیف ({len(assignments)})")

    def _load_contents(self) -> None:
        """بارگذاری فایل‌ها."""
        if not self._course:
            return

        layout = self.contents_container._content_layout
        self._clear_layout(layout)

        try:
            with Database(self.db_path) as db:
                repo = ContentRepository(db)
                contents = repo.get_by_course(self._course.group_id)
        except Exception as e:
            layout.addWidget(QLabel(f"خطا: {e}"))
            return

        if not contents:
            empty = QLabel("📭  هنوز فایلی در این درس نیست.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return

        for c in contents:
            # یک QFrame ساده برای فایل
            frame = QFrame()
            frame.setObjectName("ContentRow")
            row = QHBoxLayout(frame)
            row.setContentsMargins(15, 10, 15, 10)

            icon = "📄" if c.content_type == "pdf" else "📦"
            label = QLabel(f"{icon}  {c.title}")
            label.setAlignment(Qt.AlignRight)
            row.addWidget(label, stretch=1)

            type_label = QLabel(f"[{c.content_type.upper()}]")
            type_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
            row.addWidget(type_label)

            from PySide6.QtWidgets import QPushButton
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            download_btn = QPushButton("⬇️ دانلود")
            download_btn.setObjectName("SecondaryButton")
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.clicked.connect(
                lambda checked, u=c.url: QDesktopServices.openUrl(QUrl(u))
            )
            row.addWidget(download_btn)

            layout.addWidget(frame)

        self.tabs.setTabText(2, f"📄 فایل‌ها ({len(contents)})")