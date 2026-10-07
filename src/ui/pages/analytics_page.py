"""Analytics Page: صفحه‌ی آمار."""

from datetime import datetime

import jdatetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.mpl_chart import MplChart


class StatBox(QFrame):
    """کارت آماری کوچک."""

    def __init__(
        self,
        value: str,
        label: str,
        icon: str = "📊",
        accent: bool = False,
        height: int = 130,
    ) -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setFixedHeight(height)  # ← fixed
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 10, 12, 10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 22pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        self.value_label = QLabel(value)
        # ⚠️ از objectName استفاده کن تا QSS رنگ رو داینامیک بده
        if accent:
            self.value_label.setObjectName("StatValueAccent")
        else:
            self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        label_widget = QLabel(label)
        label_widget.setObjectName("StatLabel")  # ← QSS
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)


class SectionTitle(QLabel):
    """عنوان بخش."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("SectionTitle")
        self.setAlignment(Qt.AlignRight)
        self.setFixedHeight(40)


class AnalyticsPage(BasePage):
    """صفحه‌ی آمار."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        super().__init__(
            title="آمار",
            subtitle="نمای کلی از فعالیت شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.scroll_widget)
        self.content_layout.addWidget(scroll, stretch=1)

        # ============================================
        # بخش ۱: آمار کلی
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📊  آمار کلی"))

        # container با ارتفاع ثابت (۲ ردیف × ۱۳۰ + spacing)
        stats_container = QFrame()
        stats_container.setObjectName("StatCard")
        stats_container.setStyleSheet(
            "QFrame#StatCard { background: transparent; border: none; }"
        )
        stats_container.setFixedHeight(130 * 2 + 12)  # ۲ ردیف + spacing

        stats_grid = QGridLayout(stats_container)
        stats_grid.setSpacing(12)
        stats_grid.setContentsMargins(0, 0, 0, 0)

        self._stat_widgets = {}
        stat_defs = [
            ("courses", "درس", "📚"),
            ("assignments", "تکلیف", "📋"),
            ("contents", "فایل", "📄"),
            ("events", "رویداد", "📅"),
            ("posts", "پست", "📢"),
            ("members", "همکلاسی", "👥"),
        ]

        for i, (key, label, icon) in enumerate(stat_defs):
            row = i // 3
            col = i % 3
            card = StatBox("۰", label, icon, accent=(i == 0), height=130)
            self._stat_widgets[key] = card
            stats_grid.addWidget(card, row, col)

        self.scroll_layout.addWidget(stats_container)

        # ============================================
        # بخش ۲: وضعیت تکالیف (Pie + Stat)
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("⏰  وضعیت تکالیف"))

        assign_container = QFrame()
        assign_container.setObjectName("StatCard")
        assign_container.setStyleSheet(
            "QFrame#StatCard { background: transparent; border: none; }"
        )
        assign_container.setFixedHeight(380)

        assign_row = QHBoxLayout(assign_container)
        assign_row.setContentsMargins(0, 0, 0, 0)
        assign_row.setSpacing(12)

        # === سمت راست: کارت‌های وضعیت (عمودی) ===
        stats_col = QVBoxLayout()
        stats_col.setSpacing(10)

        self._assign_widgets = {}
        for key, label, icon in [
            ("done", "انجام‌شده", "✅"),
            ("pending", "در انتظار", "⏳"),
            ("past", "گذشته", "❌"),
        ]:
            card = StatBox("۰", label, icon, height=110)
            self._assign_widgets[key] = card
            stats_col.addWidget(card)

        stats_col.addStretch()

        stats_wrapper = QWidget()
        stats_wrapper.setLayout(stats_col)
        stats_wrapper.setFixedWidth(400)
        assign_row.addWidget(stats_wrapper)

        # === سمت چپ: Pie chart ===
        self.pie_chart = MplChart(width=5, height=4)
        self.pie_chart.setMinimumHeight(360)
        assign_row.addWidget(self.pie_chart, stretch=1)

        self.scroll_layout.addWidget(assign_container)

        # ============================================
        # بخش ۳: تکالیف به تفکیک درس (Bar)
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📈  تکالیف به تفکیک درس"))

        bar_container = QFrame()
        bar_container.setObjectName("StatCard")
        bar_container.setFixedHeight(400)

        bar_layout = QVBoxLayout(bar_container)
        bar_layout.setContentsMargins(8, 8, 8, 8)

        self.bar_chart = MplChart(width=10, height=4)
        self.bar_chart.setMinimumHeight(380)
        bar_layout.addWidget(self.bar_chart)

        self.scroll_layout.addWidget(bar_container)

        # ============================================
        # بخش ۴: نزدیک‌ترین مهلت‌ها
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("🔥  نزدیک‌ترین مهلت‌ها"))

        self.deadlines_container = QVBoxLayout()
        self.deadlines_container.setSpacing(8)
        self.deadlines_container.setContentsMargins(0, 0, 0, 8)
        self.scroll_layout.addLayout(self.deadlines_container)

        self.scroll_layout.addSpacing(20)

    def refresh(self) -> None:
        """بارخوانی آمار."""
        if not hasattr(self, "_stat_widgets"):
            return

        try:
            with Database(self.db_path) as db:
                # === آمار کلی ===
                from src.storage.repositories import (
                    QueraAssignmentRepository,
                    QueraCourseRepository,
                )
                from src.utils.quera_adapter import quera_to_assignment

                # === آمار کلی ===
                courses = CourseRepository(db).get_all()
                quera_courses = QueraCourseRepository(db).get_all()

                lms_assignments = AssignmentRepository(db).get_all()
                quera_assignments = QueraAssignmentRepository(db).get_all()
                quera_as_assignments = [
                    quera_to_assignment(q) for q in quera_assignments
                ]
                assignments = lms_assignments + quera_as_assignments

                contents = ContentRepository(db).get_all()
                events = EventRepository(db).get_all()
                posts = PostRepository(db).get_all()
                members = MemberRepository(db).get_all()

                # مجموع دروس (LMS + Quera)
                total_courses = len(courses) + len(quera_courses)

                self._set_stat("courses", total_courses)
                self._set_stat("assignments", len(assignments))
                self._set_stat("contents", len(contents))
                self._set_stat("events", len(events))
                self._set_stat("posts", len(posts))
                self._set_stat("members", len(members))

                # === وضعیت تکالیف ===
                now = datetime.now()
                done = 0
                pending = 0
                past = 0

                for a in assignments:
                    has_response = (
                        hasattr(a, "response_count")
                        and a.response_count > 0
                    )
                    if has_response:
                        done += 1
                    elif a.deadline is None:
                        pending += 1
                    elif a.deadline >= now:
                        pending += 1
                    else:
                        past += 1

                self._assign_widgets["done"].value_label.setText(
                    self._to_fa(done)
                )
                self._assign_widgets["pending"].value_label.setText(
                    self._to_fa(pending)
                )
                self._assign_widgets["past"].value_label.setText(
                    self._to_fa(past)
                )

                # === Pie chart ===
                c = CurrentTheme.colors()
                self.pie_chart.plot_pie(
                    {
                        "انجام‌شده": done,
                        "در انتظار": pending,
                        "گذشته": past,
                    },
                    title="",
                    colors=[c.SUCCESS, c.WARNING, c.ERROR],
                )

                # === تکالیف به تفکیک درس ===
                assignments_by_course: dict[str, int] = {}
                for a in assignments:
                    assignments_by_course[a.course_id] = (
                        assignments_by_course.get(a.course_id, 0) + 1
                    )

                course_map = {c2.id: c2 for c2 in courses}

                sorted_courses = sorted(
                    assignments_by_course.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )

                # اسم کوتاه‌تر برای bar chart
                bar_data: dict[str, int] = {}
                for course_id, count in sorted_courses[:8]:
                    course = course_map.get(course_id)
                    name = course.name if course else course_id
                    if len(name) > 18:
                        name = name[:15] + "..."
                    bar_data[name] = count

                self.bar_chart.plot_bar(
                    bar_data,
                    title="",
                    horizontal=True,
                )

                # === نزدیک‌ترین مهلت‌ها ===
                self._clear_layout(self.deadlines_container)

                upcoming = [
                    a for a in assignments
                    if a.deadline and a.deadline >= now
                ]
                upcoming.sort(key=lambda a: a.deadline)

                if upcoming:
                    for a in upcoming[:5]:
                        self.deadlines_container.addWidget(
                            self._make_deadline_row(a, course_map)
                        )
                else:
                    empty = QLabel("هیچ مهلت نزدیکی نیست")
                    empty.setStyleSheet(
                        f"color: {CurrentTheme.colors().TEXT_MUTED}; "
                        "padding: 12px; background: transparent;"
                    )
                    empty.setAlignment(Qt.AlignCenter)
                    self.deadlines_container.addWidget(empty)

        except Exception as e:
            print(f"❌ خطا در بارگذاری آمار: {e}")
            import traceback
            traceback.print_exc()

    def _make_deadline_row(self, assignment, course_map: dict) -> QFrame:
        """ساخت ردیف مهلت."""
        c = CurrentTheme.colors()

        frame = QFrame()
        frame.setObjectName("CourseCard")
        frame.setFixedHeight(64)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 16pt; background: transparent;")
        layout.addWidget(icon)

        course = course_map.get(assignment.course_id)
        course_name = course.name if course else ""

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel(assignment.title)
        title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 600; font-size: 11pt; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignRight)
        title_col.addWidget(title)

        sub = QLabel(course_name)
        sub.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; background: transparent;"
        )
        sub.setAlignment(Qt.AlignRight)
        title_col.addWidget(sub)

        layout.addLayout(title_col, stretch=1)

        delta = assignment.deadline - datetime.now()
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            time_text = f"{self._to_fa(days)} روز"
            color = c.PRIMARY
        elif hours > 0:
            time_text = f"{self._to_fa(hours)} ساعت"
            color = c.WARNING
        else:
            time_text = "کمتر از ۱ ساعت"
            color = c.ERROR

        time_label = QLabel(time_text)
        time_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 11pt; "
            "background: transparent;"
        )
        layout.addWidget(time_label)

        return frame

    def _set_stat(self, key: str, value: int) -> None:
        if key in self._stat_widgets:
            self._stat_widgets[key].value_label.setText(self._to_fa(value))

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    @staticmethod
    def _to_fa(n: int) -> str:
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))