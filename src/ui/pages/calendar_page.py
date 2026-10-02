"""Calendar Page: تقویم هفتگی ددلاین‌ها با پنل جزئیات."""

from collections import defaultdict
from datetime import timedelta

import jdatetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from src.models.assignment import Assignment
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.widgets.calendar_day_cell import CalendarDayCell
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.theme import Colors, CurrentTheme


class CalendarPage(BasePage):
    """صفحه‌ی تقویم ددلاین‌ها."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._assignments: list[Assignment] = []
        self._week_start: jdatetime.date = self._get_week_start(jdatetime.date.today())
        self._selected_date: jdatetime.date | None = None
        self._course_names: dict[str, str] = {}
        self._cells: list[CalendarDayCell] = []

        super().__init__(
            title="تقویم ددلاین‌ها",
            subtitle="مهلت تکالیف در این هفته",
            parent=parent,
        )
        self.refresh()

    @staticmethod
    def _get_week_start(date: jdatetime.date) -> jdatetime.date:
        offset = date.weekday()
        return date - timedelta(days=offset)

    @staticmethod
    def _format_jalali_short(jdate: jdatetime.date) -> str:
        months = [
            "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        return f"{jdate.day} {months[jdate.month]}"

    @staticmethod
    def _format_jalali_full(jdate: jdatetime.date) -> str:
        months = [
            "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        weekday = jdate.strftime("%A")
        return f"{weekday} {jdate.day} {months[jdate.month]} {jdate.year}"

    def _build(self) -> None:
        super()._build()

        # === Toolbar ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.setDirection(QHBoxLayout.RightToLeft)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("FilterButton")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._on_prev_week)
        toolbar.addWidget(self.btn_prev)

        self.week_label = QLabel("—")
        self.week_label.setAlignment(Qt.AlignCenter)
        self.week_label.setStyleSheet(
            f"color: {CurrentTheme.colors().TEXT_PRIMARY}; "
            "font-weight: bold; font-size: 12pt; background: transparent;"
        )
        toolbar.addWidget(self.week_label, stretch=1)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("FilterButton")
        self.btn_next.setFixedWidth(40)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._on_next_week)
        toolbar.addWidget(self.btn_next)

        self.btn_today = QPushButton("📅 امروز")
        self.btn_today.setObjectName("PrimaryButton")
        self.btn_today.setCursor(Qt.PointingHandCursor)
        self.btn_today.clicked.connect(self._on_today)
        toolbar.addWidget(self.btn_today)

        self.content_layout.addLayout(toolbar)

        # === Counter ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.counter_label.setStyleSheet("font-size: 9pt;")
        self.counter_label.setLayoutDirection(Qt.RightToLeft)
        self.content_layout.addWidget(self.counter_label)

        # === Grid ===
        grid_container = QFrame()
        grid_container.setObjectName("CalendarGrid")
        grid_container.setFixedHeight(155)
        grid_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid_container.setLayoutDirection(Qt.RightToLeft)

        self.grid_layout = QHBoxLayout(grid_container)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setDirection(QHBoxLayout.RightToLeft)

        self.content_layout.addWidget(grid_container)

        # === Detail Panel ===
        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("DetailPanel")
        self.detail_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum,
        )
        self.detail_panel.setMinimumHeight(300)
        self.detail_panel.setLayoutDirection(Qt.RightToLeft)

        detail_outer = QVBoxLayout(self.detail_panel)
        detail_outer.setContentsMargins(0, 0, 0, 0)
        detail_outer.setSpacing(0)
        detail_outer.setDirection(QVBoxLayout.TopToBottom)

        self.detail_header = QLabel("—")
        self.detail_header.setObjectName("DetailHeader")
        self.detail_header.setAlignment(Qt.AlignRight)
        self.detail_header.setLayoutDirection(Qt.RightToLeft)
        self.detail_header.setStyleSheet(
            f"color: {Colors.PRIMARY}; font-weight: bold; font-size: 11pt; "
            "padding: 10px 15px; background: transparent;"
        )
        detail_outer.addWidget(self.detail_header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {Colors.BORDER}; max-height: 1px;")
        detail_outer.addWidget(sep)

        self.detail_widget = QWidget()
        self.detail_widget.setLayoutDirection(Qt.RightToLeft)

        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setSpacing(10)
        self.detail_layout.setContentsMargins(15, 15, 15, 15)
        self.detail_layout.setAlignment(Qt.AlignTop)
        self.detail_layout.setDirection(QVBoxLayout.TopToBottom)

        detail_outer.addWidget(self.detail_widget, stretch=1)

        self.content_layout.addWidget(self.detail_panel)

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._assignments = AssignmentRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_names = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return

        if self._selected_date is None:
            self._selected_date = jdatetime.date.today()

        self._render_week()
        self._render_detail()

    def _render_week(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()

        today = jdatetime.date.today()
        week_start = self._week_start
        week_end = week_start + timedelta(days=6)

        self.week_label.setText(
            f"📅  {self._format_jalali_short(week_start)} تا {self._format_jalali_short(week_end)}"
        )
        self.week_label.setStyleSheet(
            f"color: {CurrentTheme.colors().TEXT_PRIMARY}; "
            "font-weight: bold; font-size: 12pt; background: transparent;"
        )

        by_day: dict[str, list[Assignment]] = defaultdict(list)
        for a in self._assignments:
            if not a.deadline:
                continue
            try:
                jdate = jdatetime.date.fromgregorian(date=a.deadline.date())
            except Exception:
                continue
            if week_start <= jdate <= week_end:
                key = jdate.strftime("%Y-%m-%d")
                by_day[key].append(a)

        total_in_week = sum(len(v) for v in by_day.values())
        self.counter_label.setText(
            f"📊  {total_in_week} ددلاین در این هفته (از {len(self._assignments)} کل)"
        )

        for i in range(7):
            day = week_start + timedelta(days=i)
            key = day.strftime("%Y-%m-%d")
            day_assignments = by_day.get(key, [])
            is_today = (day == today)
            is_selected = (day == self._selected_date)

            cell = CalendarDayCell(
                jalali_date=day,
                assignments=day_assignments,
                is_today=is_today,
                is_selected=is_selected,
            )
            cell.day_clicked.connect(self._on_day_clicked)
            cell.event_clicked.connect(self._on_event_clicked)
            self._cells.append(cell)
            self.grid_layout.addWidget(cell, stretch=1)

    def _render_detail(self) -> None:
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._selected_date:
            self.detail_header.setText("—")
            return

        header_text = self._format_jalali_full(self._selected_date)
        self.detail_header.setText(f"📋  {header_text}")

        day_assignments = []
        for a in self._assignments:
            if not a.deadline:
                continue
            try:
                jdate = jdatetime.date.fromgregorian(date=a.deadline.date())
            except Exception:
                continue
            if jdate == self._selected_date:
                day_assignments.append(a)

        if not day_assignments:
            empty = QLabel("📭  هیچ ددلاینی در این روز نیست.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("padding: 30px;")
            self.detail_layout.addWidget(empty)
            return

        for a in day_assignments:
            card = AssignmentCard(a)
            self.detail_layout.addWidget(card)

    def _on_day_clicked(self, jdate) -> None:
        self._selected_date = jdate
        for cell in self._cells:
            cell.set_selected(cell._jalali_date == jdate)
        self._render_detail()

    def _on_event_clicked(self, assignment_id: str) -> None:
        for a in self._assignments:
            if a.id == assignment_id and a.deadline:
                try:
                    jdate = jdatetime.date.fromgregorian(date=a.deadline.date())
                    self._on_day_clicked(jdate)
                except Exception:
                    pass
                break

    def _on_prev_week(self) -> None:
        self._week_start -= timedelta(days=7)
        self._render_week()

    def _on_next_week(self) -> None:
        self._week_start += timedelta(days=7)
        self._render_week()

    def _on_today(self) -> None:
        self._week_start = self._get_week_start(jdatetime.date.today())
        self._selected_date = jdatetime.date.today()
        self._render_week()
        self._render_detail()