

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.models.assignment import Assignment
from src.models.quera_assignment import QueraAssignment
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    QueraAssignmentRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.quera_assignment_card import QueraAssignmentCard


class AssignmentsPage(BasePage):
    """صفحه‌ی تکالیف (LMS + Quera)."""

    assignment_clicked = Signal(str)
    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._lms_assignments: list[Assignment] = []
        self._quera_assignments: list[QueraAssignment] = []
        self._source_filter: str = "all"  # all | lms | quera
        self._time_filter: str = "upcoming"  # upcoming | all | overdue
        self._course_names: dict[str, str] = {}

        super().__init__(
            title="تکالیف",
            subtitle="همه تکالیف (LMS + Quera)",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Source Tabs (LMS/Quera) ===
        source_toolbar = QHBoxLayout()
        source_toolbar.setSpacing(10)

        self.btn_all_sources = QPushButton("🌐 همه")
        self.btn_all_sources.setObjectName("FilterButton")
        self.btn_all_sources.setCheckable(True)
        self.btn_all_sources.setChecked(True)
        self.btn_all_sources.clicked.connect(
            lambda: self._set_source_filter("all")
        )
        source_toolbar.addWidget(self.btn_all_sources)

        self.btn_lms = QPushButton("🎓 LMS")
        self.btn_lms.setObjectName("FilterButton")
        self.btn_lms.setCheckable(True)
        self.btn_lms.clicked.connect(lambda: self._set_source_filter("lms"))
        source_toolbar.addWidget(self.btn_lms)

        self.btn_quera = QPushButton("🎯 کوئرا")
        self.btn_quera.setObjectName("FilterButton")
        self.btn_quera.setCheckable(True)
        self.btn_quera.clicked.connect(lambda: self._set_source_filter("quera"))
        source_toolbar.addWidget(self.btn_quera)

        source_toolbar.addStretch()
        self.content_layout.addLayout(source_toolbar)

        # === Time Tabs (Upcoming/All/Overdue) ===
        time_toolbar = QHBoxLayout()
        time_toolbar.setSpacing(10)

        self.btn_upcoming = QPushButton("⏰ آینده")
        self.btn_upcoming.setObjectName("FilterButton")
        self.btn_upcoming.setCheckable(True)
        self.btn_upcoming.setChecked(True)
        self.btn_upcoming.clicked.connect(lambda: self._set_time_filter("upcoming"))
        time_toolbar.addWidget(self.btn_upcoming)

        self.btn_all_time = QPushButton("📋 همه")
        self.btn_all_time.setObjectName("FilterButton")
        self.btn_all_time.setCheckable(True)
        self.btn_all_time.clicked.connect(lambda: self._set_time_filter("all"))
        time_toolbar.addWidget(self.btn_all_time)

        self.btn_overdue = QPushButton("⏹️ گذشته")
        self.btn_overdue.setObjectName("FilterButton")
        self.btn_overdue.setCheckable(True)
        self.btn_overdue.clicked.connect(lambda: self._set_time_filter("overdue"))
        time_toolbar.addWidget(self.btn_overdue)

        time_toolbar.addStretch()
        self.content_layout.addLayout(time_toolbar)

        # Counter
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.content_layout.addWidget(self.counter_label)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(
            self.list_widget.sizePolicy().horizontalPolicy(),
            self.list_widget.sizePolicy().verticalPolicy(),
        )
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._lms_assignments = AssignmentRepository(db).get_all()
                self._quera_assignments = QueraAssignmentRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_names = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        # === فیلتر منبع ===
        lms = list(self._lms_assignments) if self._source_filter in ("all", "lms") else []
        quera = list(self._quera_assignments) if self._source_filter in ("all", "quera") else []

        # === فیلتر زمان ===
        now = datetime.now()

        def is_upcoming(deadline):
            return deadline and deadline >= now

        def is_overdue(deadline):
            return deadline and deadline < now

        if self._time_filter == "upcoming":
            lms = [a for a in lms if is_upcoming(a.deadline)]
            quera = [a for a in quera if is_upcoming(a.finish_time)]
        elif self._time_filter == "overdue":
            lms = [a for a in lms if is_overdue(a.deadline)]
            quera = [a for a in quera if is_overdue(a.finish_time)]

        total = len(lms) + len(quera)
        total_all = (
            len(self._lms_assignments)
            if self._source_filter == "lms"
            else len(self._quera_assignments)
            if self._source_filter == "quera"
            else len(self._lms_assignments) + len(self._quera_assignments)
        )

        self.counter_label.setText(
            f"نمایش {total} از {total_all} تکلیف"
        )

        # پاک
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        if not lms and not quera:
            from src.ui.widgets.empty_state import EmptyState
            empty = EmptyState(
                icon_name="clipboard-list",
                title="هیچ تکلیفی نیست",
                description="برای این فیلتر، تکلیفی پیدا نشد. یک Sync جدید بزنید.",
                action_text="🔄  بروزرسانی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)
            self.list_layout.addWidget(empty)
            return

        # === ترکیب و مرتب‌سازی بر اساس deadline ===
        items = []

        for a in lms:
            deadline = a.deadline or datetime.max
            items.append((deadline, "lms", a))

        for q in quera:
            deadline = q.finish_time or datetime.max
            items.append((deadline, "quera", q))

        items.sort(key=lambda x: x[0])

        # === رندر ===
        for deadline, source, item in items:
            if source == "lms":
                # LMS: با هدر نام درس
                container = QFrame()
                c_layout = QVBoxLayout(container)
                c_layout.setContentsMargins(0, 0, 0, 0)
                c_layout.setSpacing(5)

                course_name = self._course_names.get(item.course_id, item.course_id)
                course_label = QLabel(f"📚  {course_name}")
                course_label.setStyleSheet(
                    f"color: {CurrentTheme.colors().PRIMARY}; "
                    "font-weight: bold; padding: 0 5px; background: transparent;"
                )
                course_label.setAlignment(Qt.AlignRight)
                c_layout.addWidget(course_label)

                card = AssignmentCard(item)
                c_layout.addWidget(card)
                self.list_layout.addWidget(container)
            else:  # quera
                card = QueraAssignmentCard(item)
                self.list_layout.addWidget(card)

    def _set_source_filter(self, f: str) -> None:
        self._source_filter = f
        self.btn_all_sources.setChecked(f == "all")
        self.btn_lms.setChecked(f == "lms")
        self.btn_quera.setChecked(f == "quera")
        self._apply_filters()

    def _set_time_filter(self, f: str) -> None:
        self._time_filter = f
        self.btn_upcoming.setChecked(f == "upcoming")
        self.btn_all_time.setChecked(f == "all")
        self.btn_overdue.setChecked(f == "overdue")
        self._apply_filters()