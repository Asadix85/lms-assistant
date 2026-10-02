"""Assignments Page: لیست همه تکالیف."""

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
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.assignment_card import AssignmentCard


class AssignmentsPage(BasePage):
    """صفحه‌ی تکالیف."""

    assignment_clicked = Signal(str)  # course_id
    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._all: list[Assignment] = []
        self._filter: str = "upcoming"  # upcoming | all | overdue
        self._course_names: dict[str, str] = {}

        super().__init__(
            title="تکالیف",
            subtitle="همه تکالیف دروس شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_upcoming = QPushButton("⏰ آینده")
        self.btn_upcoming.setObjectName("FilterButton")
        self.btn_upcoming.setCheckable(True)
        self.btn_upcoming.setChecked(True)
        self.btn_upcoming.clicked.connect(lambda: self._set_filter("upcoming"))
        toolbar.addWidget(self.btn_upcoming)

        self.btn_all = QPushButton("📋 همه")
        self.btn_all.setObjectName("FilterButton")
        self.btn_all.setCheckable(True)
        self.btn_all.clicked.connect(lambda: self._set_filter("all"))
        toolbar.addWidget(self.btn_all)

        self.btn_overdue = QPushButton("⏹️ گذشته")
        self.btn_overdue.setObjectName("FilterButton")
        self.btn_overdue.setCheckable(True)
        self.btn_overdue.clicked.connect(lambda: self._set_filter("overdue"))
        toolbar.addWidget(self.btn_overdue)

        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

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
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._all = AssignmentRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_names = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        assignments = list(self._all)
        now = datetime.now()

        if self._filter == "upcoming":
            assignments = [
                a for a in assignments
                if a.deadline and a.deadline >= now
            ]
        elif self._filter == "overdue":
            assignments = [
                a for a in assignments
                if a.deadline and a.deadline < now
            ]

        self.counter_label.setText(
            f"نمایش {len(assignments)} از {len(self._all)} تکلیف"
        )

        # پاک
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not assignments:
            from src.ui.widgets.empty_state import EmptyState
            empty = EmptyState(
                icon_name="clipboard-list",
                title="هیچ تکلیفی نیست",
                description="هنوز تکلیفی برای این فیلتر پیدا نشده. یک Sync جدید بزنید.",
                action_text="🔄  بروزرسانی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)  # ← Signal جدید
            self.list_layout.addWidget(empty)
            return

        # مرتب بر اساس ددلاین
        assignments.sort(key=lambda a: a.deadline or datetime.max)

        for a in assignments:
            # Container با نام درس
            container = QFrame()
            container.setObjectName("AssignmentContainer")
            c_layout = QVBoxLayout(container)
            c_layout.setContentsMargins(0, 0, 0, 0)
            c_layout.setSpacing(5)

            # نام درس
            course_name = self._course_names.get(a.course_id, a.course_id)
            course_label = QLabel(f"📚  {course_name}")
            course_label.setStyleSheet(
                f"color: {Colors.PRIMARY}; font-weight: bold; "
                "padding: 0 5px; background: transparent;"
            )
            course_label.setAlignment(Qt.AlignRight)
            c_layout.addWidget(course_label)

            # کارت
            card = AssignmentCard(a)
            c_layout.addWidget(card)

            self.list_layout.addWidget(container)

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_upcoming.setChecked(f == "upcoming")
        self.btn_all.setChecked(f == "all")
        self.btn_overdue.setChecked(f == "overdue")
        self._apply_filters()