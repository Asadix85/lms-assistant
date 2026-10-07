"""Courses Page: نمایش دروس LMS + کلاس‌های Quera."""

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
from src.models.quera_course import QueraCourse
from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
    QueraCourseRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.course_card import CourseCard
from src.ui.widgets.quera_course_card import QueraCourseCard


class CoursesPage(BasePage):
    """صفحه‌ی دروس (LMS + Quera)."""

    course_selected = Signal(str)
    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._lms_courses: list[Course] = []
        self._quera_courses: list[QueraCourse] = []
        self._filter_domain: str | None = None
        self._filter_active: bool = False
        self._search_text: str = ""

        super().__init__(
            title="دروس",
            subtitle="همه‌ی دروس شما (LMS + Quera)",
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
        self.search_input.setPlaceholderText(
            "🔍  جستجو برای نام درس، استاد یا کد..."
        )
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

        # ⚠️ دکمه‌ی کوئرا (جدید)
        self.btn_quera = QPushButton("🎯 کوئرا")
        self.btn_quera.setObjectName("FilterButton")
        self.btn_quera.setCheckable(True)
        self.btn_quera.clicked.connect(lambda: self._set_filter("quera"))
        toolbar.addWidget(self.btn_quera)

        self.btn_active = QPushButton("✓ فعال")
        self.btn_active.setObjectName("FilterButton")
        self.btn_active.setCheckable(True)
        self.btn_active.setChecked(False)
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
        """بارخوانی دروس LMS + کلاس‌های Quera."""
        try:
            with Database(self.db_path) as db:
                self._lms_courses = CourseRepository(db).get_all()
                self._quera_courses = QueraCourseRepository(db).get_all()
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return

        self._apply_filters()

    def _apply_filters(self) -> None:
        """اعمال فیلترها و رندر."""
        lms = list(self._lms_courses)
        quera = list(self._quera_courses)

        # === فیلتر domain ===
        if self._filter_domain == "quera":
            lms = []
        elif self._filter_domain:  # lms3 یا lms4
            quera = []
            lms = [c for c in lms if c.domain == self._filter_domain]

        # === فیلتر active ===
        if self._filter_active:
            lms = [c for c in lms if c.status == CourseStatus.ACTIVE]
            quera = [c for c in quera if c.is_active]

        # === جستجو ===
        if self._search_text:
            s = self._search_text.lower()
            lms = [
                c for c in lms
                if s in c.name.lower()
                or s in (c.teacher or "").lower()
                or s in (c.code or "").lower()
            ]
            quera = [
                c for c in quera
                if s in c.name.lower()
                or s in (c.teacher or "").lower()
            ]

        total = len(lms) + len(quera)
        total_all = len(self._lms_courses) + len(self._quera_courses)

        self.counter_label.setText(
            f"نمایش {total} از {total_all} درس"
        )

        # پاک کردن grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not lms and not quera:
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

        # === ترکیب: LMS اول، بعد Quera ===
        items = []
        for c in lms:
            items.append(("lms", c))
        for q in quera:
            items.append(("quera", q))

        columns = 3
        for i, (source, item) in enumerate(items):
            row = i // columns
            col = i % columns

            if source == "lms":
                card = CourseCard(item)
                card.clicked.connect(self.course_selected.emit)
            else:  # quera
                card = QueraCourseCard(item)
                card.clicked.connect(self._on_quera_course_clicked)

            self.grid_layout.addWidget(card, row, col)

    def _on_sync_requested(self) -> None:
        self.sync_requested.emit()

    def _on_quera_course_clicked(self, synthetic_id: str) -> None:
        """کلیک روی کلاس Quera → باز کردن توی مرورگر."""
        # فقط id واقعی
        quera_id = synthetic_id.replace("quera_", "")
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(
            QUrl(f"https://quera.org/course/{quera_id}")
        )

    # === Events ===

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text
        self._apply_filters()

    def _set_filter(self, domain: str | None) -> None:
        self._filter_domain = domain
        self.btn_all.setChecked(domain is None)
        self.btn_lms3.setChecked(domain == "lms3")
        self.btn_lms4.setChecked(domain == "lms4")
        self.btn_quera.setChecked(domain == "quera")
        self._apply_filters()

    def _toggle_active(self) -> None:
        self._filter_active = self.btn_active.isChecked()
        self._apply_filters()