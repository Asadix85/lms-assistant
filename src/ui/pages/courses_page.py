"""Courses Page: نمایش دروس به صورت کارت."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.models.course import Course, CourseStatus
from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.course_card import CourseCard


class CoursesPage(BasePage):
    """صفحه‌ی دروس."""

    course_selected = Signal(str)  # course_id
    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._all_courses: list[Course] = []
        self._filter_domain: str | None = None
        self._filter_active: bool = False
        self._search_text: str = ""

        super().__init__(
            title="دروس",
            subtitle="همه‌ی دروس شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Toolbar ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  جستجو برای نام درس، استاد یا کد...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_input, stretch=1)

        # Filters
        self.btn_all = QPushButton("همه")
        self.btn_all.setObjectName("FilterButton")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self._set_filter(None))
        toolbar.addWidget(self.btn_all)

        self.btn_lms3 = QPushButton("🟢 lms3")
        self.btn_lms3.setObjectName("FilterButton")
        self.btn_lms3.setCheckable(True)
        self.btn_lms3.clicked.connect(lambda: self._set_filter("lms3"))
        toolbar.addWidget(self.btn_lms3)

        self.btn_lms4 = QPushButton("🔵 lms4")
        self.btn_lms4.setObjectName("FilterButton")
        self.btn_lms4.setCheckable(True)
        self.btn_lms4.clicked.connect(lambda: self._set_filter("lms4"))
        toolbar.addWidget(self.btn_lms4)

        self.btn_active = QPushButton("✓ فعال")
        self.btn_active.setObjectName("FilterButton")
        self.btn_active.setCheckable(True)
        self.btn_active.clicked.connect(self._toggle_active)
        toolbar.addWidget(self.btn_active)

        self.content_layout.addLayout(toolbar)

        # === Counter ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.content_layout.addWidget(self.counter_label)

        # === Scroll Area with Grid ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        scroll.setWidget(self.grid_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    # === Data ===

    def refresh(self) -> None:
        """بارخوانی دروس از دیتابیس."""
        try:
            with Database(self.db_path) as db:
                repo = CourseRepository(db)
                self._all_courses = repo.get_all()
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return

        self._apply_filters()

    def _apply_filters(self) -> None:
        """اعمال فیلترها و رندر."""
        # فیلتر
        courses = self._all_courses

        if self._filter_domain:
            courses = [c for c in courses if c.domain == self._filter_domain]

        if self._filter_active:
            courses = [c for c in courses if c.status == CourseStatus.ACTIVE]

        if self._search_text:
            s = self._search_text.lower()
            courses = [
                c for c in courses
                if s in c.name.lower()
                or s in (c.teacher or "").lower()
                or s in (c.code or "").lower()
            ]

        # Counter
        self.counter_label.setText(f"نمایش {len(courses)} از {len(self._all_courses)} درس")

        # پاک کردن grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # رندر
        if not courses:
            from src.ui.widgets.empty_state import EmptyState
            empty = EmptyState(
                icon_name="magnifying-glass",
                title="هیچ درسی پیدا نشد",
                description="فیلترها را تغییر دهید یا یک Sync جدید بزنید.",
                action_text="🔄  بروزرسانی",
            )
            empty.action_clicked.connect(self._on_sync_requested)
            self.grid_layout.addWidget(empty, 0, 0, 1, 3)
            return

        columns = 3
        for i, c in enumerate(courses):
            row = i // columns
            col = i % columns
            card = CourseCard(c)
            card.clicked.connect(self.course_selected.emit)
            self.grid_layout.addWidget(card, row, col)

    def _on_sync_requested(self) -> None:
        self.sync_requested.emit()

    # === Events ===

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text
        self._apply_filters()

    def _set_filter(self, domain: str | None) -> None:
        self._filter_domain = domain
        # به‌روزرسانی دکمه‌ها
        self.btn_all.setChecked(domain is None)
        self.btn_lms3.setChecked(domain == "lms3")
        self.btn_lms4.setChecked(domain == "lms4")
        self._apply_filters()

    def _toggle_active(self) -> None:
        self._filter_active = self.btn_active.isChecked()
        self._apply_filters()