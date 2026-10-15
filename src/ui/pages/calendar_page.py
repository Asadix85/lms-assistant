"""Calendar Page: تقویم هفتگی ددلاین‌ها — نسخه‌ی بازطراحی‌شده (خفن!)."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

import jdatetime
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QGraphicsOpacityEffect,
)

from src.models.assignment import Assignment
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    QueraAssignmentRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.calendar_day_cell import CalendarDayCell


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CalendarPage(BasePage):
    """صفحه‌ی تقویم ددلاین‌ها — طراحی مدرن با پنل جزئیات."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._assignments: list[Assignment] = []
        self._week_start: jdatetime.date = self._get_week_start(jdatetime.date.today())
        self._selected_date: jdatetime.date | None = None
        self._course_names: dict[str, str] = {}
        self._cells: list[CalendarDayCell] = []
        self._anims: list = []
        self._first_load = True

        super().__init__(
            title="تقویم ددلاین‌ها",
            subtitle="مهلت تکالیف در این هفته",
            parent=parent,
        )
        self.refresh()

    @staticmethod
    def _get_week_start(date: jdatetime.date) -> jdatetime.date:
        return date - timedelta(days=date.weekday())

    @staticmethod
    def _format_jalali_short(jdate: jdatetime.date) -> str:
        months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        return f"{jdate.day} {months[jdate.month]}"

    @staticmethod
    def _format_jalali_full(jdate: jdatetime.date) -> str:
        months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        weekdays = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        return f"{weekdays[jdate.weekday()]} — {jdate.day} {months[jdate.month]} {jdate.year}"

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        # === نوار ناوبری هفته با گرادینت ===
        nav_card = QFrame()
        nav_card.setObjectName("Card")
        nav_lay = QHBoxLayout(nav_card)
        nav_lay.setContentsMargins(16, 12, 16, 12)
        nav_lay.setSpacing(12)

        self.btn_prev = self._nav_btn("→")
        self.btn_prev.clicked.connect(self._on_prev_week)
        nav_lay.addWidget(self.btn_prev)

        self.week_label = QLabel("—")
        self.week_label.setAlignment(Qt.AlignCenter)
        self.week_label.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 800; "
            "font-size: 13pt; background: transparent;"
        )
        nav_lay.addWidget(self.week_label, stretch=1)

        self.btn_next = self._nav_btn("←")
        self.btn_next.clicked.connect(self._on_next_week)
        nav_lay.addWidget(self.btn_next)

        self.btn_today = QPushButton("📅  امروز")
        self.btn_today.setObjectName("PrimaryButton")
        self.btn_today.setCursor(Qt.PointingHandCursor)
        self.btn_today.setFixedHeight(38)
        self.btn_today.clicked.connect(self._on_today)
        nav_lay.addWidget(self.btn_today)

        self.content_layout.addWidget(nav_card)

        # === نوار آمار هفتگی ===
        stats_row = QHBoxLayout()
        stats_row.setContentsMargins(4, 8, 4, 0)
        stats_row.setSpacing(10)

        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        stats_row.addWidget(self.counter_label)
        stats_row.addStretch()

        self.stats_pills = QHBoxLayout()
        self.stats_pills.setSpacing(8)
        stats_row.addLayout(self.stats_pills)
        self.content_layout.addLayout(stats_row)

        # === گرید هفته ===
        self.grid_container = QFrame()
        grid_container = self.grid_container
        grid_container.setObjectName("CalendarGrid")
        grid_container.setFixedHeight(180)
        grid_bg = "rgba(28, 38, 38, 0.75)" if CurrentTheme.is_dark() else "#FFFFFF"
        grid_container.setStyleSheet(f"""
            QFrame#CalendarGrid {{
                background-color: {grid_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
        """)

        self.grid_layout = QHBoxLayout(grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.addWidget(grid_container)

        # === پنل جزئیات ===
        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("DetailPanel")
        self.detail_panel.setMinimumHeight(320)
        detail_bg = "rgba(28, 38, 38, 0.75)" if CurrentTheme.is_dark() else "#FFFFFF"
        self.detail_panel.setStyleSheet(f"""
            QFrame#DetailPanel {{
                background-color: {detail_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
        """)

        detail_outer = QVBoxLayout(self.detail_panel)
        detail_outer.setContentsMargins(0, 0, 0, 0)
        detail_outer.setSpacing(0)

        # هدر پنل
        self.detail_header_frame = QFrame()
        header_gradient_start = "rgba(42, 166, 163, 0.20)" if CurrentTheme.is_dark() else "rgba(42, 166, 163, 0.10)"
        self.detail_header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {header_gradient_start},
                    stop:1 transparent);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }}
        """)
        header_lay = QHBoxLayout(self.detail_header_frame)
        header_lay.setContentsMargins(18, 14, 18, 14)
        header_lay.setSpacing(10)

        header_icon = QLabel("📋")
        header_icon.setStyleSheet("font-size: 14pt; background: transparent;")
        header_lay.addWidget(header_icon)

        self.detail_header = QLabel("—")
        self.detail_header.setStyleSheet(
            f"color: {_c('PRIMARY', '#2AA6A3')}; font-weight: 800; "
            "font-size: 12pt; background: transparent;"
        )
        header_lay.addWidget(self.detail_header, stretch=1)
        detail_outer.addWidget(self.detail_header_frame)

        # جداکننده
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};")
        detail_outer.addWidget(sep)

        # محتوای پنل با اسکرول
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setSpacing(10)
        self.detail_layout.setContentsMargins(16, 16, 16, 16)
        self.detail_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.detail_widget)
        detail_outer.addWidget(scroll, stretch=1)

        self.content_layout.addWidget(self.detail_panel, stretch=1)

    def _fix_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)
        for obj in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj)
            if lbl:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم، همه ویجت‌ها رو به‌روز کن."""
        # به‌روزرسانی گرید
        is_dark = CurrentTheme.is_dark()
        grid_bg = "rgba(28, 38, 38, 0.75)" if is_dark else "#FFFFFF"
        self.grid_container.setStyleSheet(f"""
            QFrame#CalendarGrid {{
                background-color: {grid_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
        """)

        # به‌روزرسانی پنل جزئیات
        detail_bg = "rgba(28, 38, 38, 0.75)" if is_dark else "#FFFFFF"
        self.detail_panel.setStyleSheet(f"""
            QFrame#DetailPanel {{
                background-color: {detail_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
        """)

        # به‌روزرسانی هدر پنل
        header_gradient_start = "rgba(42, 166, 163, 0.20)" if is_dark else "rgba(42, 166, 163, 0.10)"
        self.detail_header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {header_gradient_start},
                    stop:1 transparent);
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }}
        """)

        # به‌روزرسانی سلول‌های روز
        for cell in self._cells:
            cell.refresh_theme()

        # رندر مجدد detail panel
        self._render_detail()

    def _nav_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(38, 38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_c('GLASS_BG', 'rgba(255,255,255,0.68)')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 19px;
                font-size: 12pt;
                font-weight: 700;
                color: {_c('TEXT_PRIMARY', '#1C1C1E')};
            }}
            QPushButton:hover {{
                background-color: {_c('PRIMARY', '#2AA6A3')};
                color: #FFFFFF;
                border-color: {_c('PRIMARY', '#2AA6A3')};
            }}
        """)
        return btn

    def refresh(self) -> None:
        from src.utils.quera_adapter import quera_to_assignment

        try:
            with Database(self.db_path) as db:
                lms_assignments = AssignmentRepository(db).get_all()
                quera_assignments = QueraAssignmentRepository(db).get_all()
                quera_as_assignments = [quera_to_assignment(q) for q in quera_assignments]
                self._assignments = lms_assignments + quera_as_assignments

                courses = CourseRepository(db).get_all()
                self._course_names = {c.id: c.name for c in courses}
                for q in quera_assignments:
                    synthetic_id = f"quera_{q.course_name}"
                    self._course_names[synthetic_id] = f"🎯 {q.course_name} (کوئرا)"
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
        self.counter_label.setText(f"📊  {total_in_week} ددلاین در این هفته")

        # پیل‌های آمار
        while self.stats_pills.count():
            item = self.stats_pills.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        from datetime import datetime as dt_cls

        now = dt_cls.now()
        overdue = sum(1 for a in self._assignments if a.deadline and a.deadline < now)
        upcoming = sum(1 for a in self._assignments if a.deadline and a.deadline >= now)

        self.stats_pills.addWidget(self._stat_pill("⏹️", "گذشته", overdue, _c("ERROR", "#FF3B30")))
        self.stats_pills.addWidget(self._stat_pill("⏰", "آینده", upcoming, _c("SUCCESS", "#34C759")))

        widgets_to_animate = []
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
            widgets_to_animate.append(cell)

        if self._first_load:
            self._fade_in(widgets_to_animate)
            self._first_load = False

    def _stat_pill(self, icon: str, label: str, count: int, color: str) -> QWidget:
        w = QFrame()
        w.setFixedHeight(28)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(6)

        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 9pt; background: transparent;")
        lay.addWidget(ic)

        lbl = QLabel(f"{label}: {count}")
        lbl.setStyleSheet(
            f"color: {color}; font-size: 8.5pt; font-weight: 700; background: transparent;"
        )
        lay.addWidget(lbl)

        w.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border-radius: 14px;
            }}
        """)
        return w

    def _render_detail(self) -> None:
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.detail_layout.setAlignment(Qt.AlignTop)

        if not self._selected_date:
            self.detail_header.setText("—")
            return

        self.detail_header.setText(self._format_jalali_full(self._selected_date))

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
            self.detail_layout.setAlignment(Qt.AlignCenter)
            self.detail_layout.addWidget(self._make_empty_detail())
            return

        from src.utils.quera_adapter import is_quera_item

        for a in day_assignments:
            if is_quera_item(a):
                container = QWidget()
                c_lay = QVBoxLayout(container)
                c_lay.setContentsMargins(0, 0, 0, 0)
                c_lay.setSpacing(6)

                course_lbl = QLabel(f"🎯  {a.course_id.replace('quera_', '')} (کوئرا)")
                course_lbl.setStyleSheet(
                    f"color: {_c('ACCENT', '#FF9500')}; font-weight: 700; "
                    "font-size: 10pt; background: transparent;"
                )
                c_lay.addWidget(course_lbl)
                c_lay.addWidget(AssignmentCard(a))
                self.detail_layout.addWidget(container)
            else:
                course_name = self._course_names.get(a.course_id, "")
                if course_name:
                    container = QWidget()
                    c_lay = QVBoxLayout(container)
                    c_lay.setContentsMargins(0, 0, 0, 0)
                    c_lay.setSpacing(6)

                    course_lbl = QLabel(f"📚  {course_name}")
                    course_lbl.setStyleSheet(
                        f"color: {_c('PRIMARY', '#2AA6A3')}; font-weight: 700; "
                        "font-size: 10pt; background: transparent;"
                    )
                    c_lay.addWidget(course_lbl)
                    c_lay.addWidget(AssignmentCard(a))
                    self.detail_layout.addWidget(container)
                else:
                    self.detail_layout.addWidget(AssignmentCard(a))

        # انیمیشن پنل
        self._fade_widget(self.detail_panel)

    def _make_empty_detail(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(8)

        icon = QLabel("📅")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 36pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;")
        lay.addWidget(icon)

        title = QLabel("هیچ ددلاینی در این روز نیست")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 11pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        desc = QLabel("روز دیگری را از تقویم انتخاب کنید.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9pt; background: transparent;"
        )
        lay.addWidget(desc)
        return w

    def _fade_in(self, widgets: list[QWidget]) -> None:
        self._anims.clear()
        for i, w in enumerate(widgets):
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(300)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda widget=w: (widget.setGraphicsEffect(None), widget.update()))
            self._anims.append(anim)
            QTimer.singleShot(i * 50, anim.start)

    def _fade_widget(self, widget: QWidget) -> None:
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(250)
        anim.setStartValue(0.3)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: (widget.setGraphicsEffect(None), widget.update()))
        anim.start()

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
        self._render_detail()

    def _on_next_week(self) -> None:
        self._week_start += timedelta(days=7)
        self._render_week()
        self._render_detail()

    def _on_today(self) -> None:
        self._week_start = self._get_week_start(jdatetime.date.today())
        self._selected_date = jdatetime.date.today()
        self._render_week()
        self._render_detail()