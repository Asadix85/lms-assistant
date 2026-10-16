"""Analytics Page: صفحه‌ی آمار — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QGraphicsOpacityEffect,
)

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
    QueraAssignmentRepository,
    QueraCourseRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.mpl_chart import MplChart
from src.utils.quera_adapter import quera_to_assignment


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class StatBox(QFrame):
    """کارت آماری کوچک با آیکون گرادیانتی."""

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
        self.setFixedHeight(height)
        self._accent = accent
        self._build(icon, value, label)

    def _card_style(self) -> str:
        """استایل کارت بر اساس تم فعلی (Design Token محور)."""
        is_dark = CurrentTheme.is_dark()
        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        return f"""
            QFrame#StatCard {{
                background-color: {card_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 14px;
            }}
            QFrame#StatCard:hover {{
                background-color: {card_hover};
                border-color: {_c('PRIMARY', '#2AA6A3')}50;
            }}
        """

    def _value_color(self) -> str:
        return _c('PRIMARY', '#2AA6A3') if self._accent else _c('TEXT_PRIMARY', '#1C1C1E')

    def _build(self, icon: str, value: str, label: str) -> None:
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        lay.setContentsMargins(12, 10, 12, 10)

        # آیکون
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20pt; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon_lbl)

        # عدد
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {self._value_color()}; font-size: 20pt; font-weight: 800; background: transparent;")
        self.value_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.value_label)

        # برچسب
        label_lbl = QLabel(label)
        label_lbl.setStyleSheet(f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9pt; background: transparent;")
        label_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(label_lbl)

        self.setStyleSheet(self._card_style())

    def refresh_theme(self) -> None:
        """بعد از تغییر تم — باگ قبلی: این متد داخل _build به‌صورت تابع تو در تعریف شده بود و هرگز به کلاس متصل نمی‌شد."""
        self.setStyleSheet(self._card_style())
        self.value_label.setStyleSheet(
            f"color: {self._value_color()}; font-size: 20pt; font-weight: 800; background: transparent;")


class SectionTitle(QLabel):
    """عنوان بخش."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("SectionTitle")
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            color: {_c('TEXT_PRIMARY', '#1C1C1E')};
            font-weight: 800;
            font-size: 13pt;
            background: transparent;
            padding: 8px 4px;
            border-bottom: 2px solid {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.15)')};
        """)


class AnalyticsPage(BasePage):
    """صفحه‌ی آمار — با نمودارهای زیبا."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._anims: list = []
        self._first_load = True
        super().__init__(
            title="آمار",
            subtitle="نمای کلی از فعالیت شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setContentsMargins(8, 8, 8, 24)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.scroll_widget)
        self.content_layout.addWidget(scroll, stretch=1)

        # ============================================
        # بخش ۱: آمار کلی
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📊  آمار کلی"))

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

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
            row, col = i // 3, i % 3
            card = StatBox("۰", label, icon, accent=(i == 0), height=130)
            self._stat_widgets[key] = card
            stats_grid.addWidget(card, row, col)
        self.scroll_layout.addLayout(stats_grid)

        # ============================================
        # بخش ۲: وضعیت تکالیف
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("⏰  وضعیت تکالیف"))

        assign_row = QHBoxLayout()
        assign_row.setSpacing(14)

        # کارت‌های وضعیت
        stats_col = QVBoxLayout()
        stats_col.setSpacing(10)

        self._assign_widgets = {}
        for key, label, icon in [("done", "انجام‌شده", "✅"), ("pending", "در انتظار", "⏳"), ("past", "گذشته", "❌")]:
            card = StatBox("۰", label, icon, height=110)
            self._assign_widgets[key] = card
            stats_col.addWidget(card)
        stats_col.addStretch()

        stats_wrapper = QWidget()
        stats_wrapper.setLayout(stats_col)
        stats_wrapper.setFixedWidth(280)
        assign_row.addWidget(stats_wrapper)

        # Pie chart
        self.pie_chart = MplChart(width=5, height=4)
        self.pie_chart.setMinimumHeight(360)
        assign_row.addWidget(self.pie_chart, stretch=1)
        self.scroll_layout.addLayout(assign_row)

        # ============================================
        # بخش ۳: تکالیف به تفکیک درس
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📈  تکالیف به تفکیک درس"))

        bar_container = QFrame()
        bar_container.setObjectName("Card")
        bar_container.setFixedHeight(400)
        bar_lay = QVBoxLayout(bar_container)
        bar_lay.setContentsMargins(12, 12, 12, 12)

        self.bar_chart = MplChart(width=10, height=4)
        self.bar_chart.setMinimumHeight(370)
        bar_lay.addWidget(self.bar_chart)
        self.scroll_layout.addWidget(bar_container)

        # ============================================
        # بخش ۴: نزدیک‌ترین مهلت‌ها
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("🔥  نزدیک‌ترین مهلت‌ها"))

        self.deadlines_container = QVBoxLayout()
        self.deadlines_container.setSpacing(10)
        self.scroll_layout.addLayout(self.deadlines_container)

        self.scroll_layout.addSpacing(20)

    def _fix_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)
        for obj in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj)
            if lbl:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        # به‌روزرسانی StatBox ها
        for widget in self._stat_widgets.values():
            widget.refresh_theme()

        for widget in self._assign_widgets.values():
            widget.refresh_theme()

        # رندر مجدد نمودارها
        self.refresh()

    def refresh(self) -> None:
        if not hasattr(self, "_stat_widgets"):
            return

        try:
            with Database(self.db_path) as db:
                courses = CourseRepository(db).get_all()
                quera_courses = QueraCourseRepository(db).get_all()

                lms_assignments = AssignmentRepository(db).get_all()
                quera_assignments = QueraAssignmentRepository(db).get_all()
                quera_as_assignments = [quera_to_assignment(q) for q in quera_assignments]
                assignments = lms_assignments + quera_as_assignments

                contents = ContentRepository(db).get_all()
                events = EventRepository(db).get_all()
                posts = PostRepository(db).get_all()
                members = MemberRepository(db).get_all()

                total_courses = len(courses) + len(quera_courses)
                self._set_stat("courses", total_courses)
                self._set_stat("assignments", len(assignments))
                self._set_stat("contents", len(contents))
                self._set_stat("events", len(events))
                self._set_stat("posts", len(posts))
                self._set_stat("members", len(members))

                # وضعیت تکالیف
                now = datetime.now()
                done = sum(1 for a in assignments if hasattr(a, "response_count") and a.response_count > 0)
                pending = sum(1 for a in assignments if not (hasattr(a, "response_count") and a.response_count > 0) and (a.deadline is None or a.deadline >= now))
                past = sum(1 for a in assignments if not (hasattr(a, "response_count") and a.response_count > 0) and a.deadline and a.deadline < now)

                self._assign_widgets["done"].value_label.setText(self._to_fa(done))
                self._assign_widgets["pending"].value_label.setText(self._to_fa(pending))
                self._assign_widgets["past"].value_label.setText(self._to_fa(past))

                # Pie chart
                c = CurrentTheme.colors()
                self.pie_chart.plot_pie(
                    {"انجام‌شده": done, "در انتظار": pending, "گذشته": past},
                    colors=[c.SUCCESS, c.WARNING, c.ERROR],
                )

                # Bar chart
                assignments_by_course: dict[str, int] = {}
                for a in assignments:
                    assignments_by_course[a.course_id] = assignments_by_course.get(a.course_id, 0) + 1

                course_map = {c2.id: c2 for c2 in courses}
                sorted_courses = sorted(assignments_by_course.items(), key=lambda x: x[1], reverse=True)

                bar_data = {}
                for course_id, count in sorted_courses[:8]:
                    course = course_map.get(course_id)
                    name = course.name if course else course_id
                    if len(name) > 18:
                        name = name[:15] + "..."
                    bar_data[name] = count
                self.bar_chart.plot_bar(bar_data, horizontal=True)

                # مهلت‌ها
                self._clear_layout(self.deadlines_container)
                upcoming = sorted([a for a in assignments if a.deadline and a.deadline >= now], key=lambda a: a.deadline)

                if upcoming:
                    for a in upcoming[:5]:
                        self.deadlines_container.addWidget(self._make_deadline_row(a, course_map))
                else:
                    empty = QLabel("هیچ مهلت نزدیکی نیست")
                    empty.setAlignment(Qt.AlignCenter)
                    empty.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; padding: 20px; background: transparent;")
                    self.deadlines_container.addWidget(empty)

        except Exception as e:
            print(f"❌ خطا در بارگذاری آمار: {e}")
            import traceback
            traceback.print_exc()

        if self._first_load:
            self._fade_in()
            self._first_load = False

    def _fade_in(self) -> None:
        self._anims.clear()
        widgets = []
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                widgets.append(item.widget())
            elif item.layout():
                for j in range(item.layout().count()):
                    sub = item.layout().itemAt(j)
                    if sub.widget():
                        widgets.append(sub.widget())

        for i, w in enumerate(widgets[:15]):
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda widget=w: (widget.setGraphicsEffect(None), widget.update()))
            self._anims.append(anim)
            QTimer.singleShot(i * 70, anim.start)

    def _make_deadline_row(self, assignment, course_map: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("CourseCard")
        frame.setFixedHeight(68)

        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(12)

        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 14pt; background: transparent;")
        lay.addWidget(icon)

        course = course_map.get(assignment.course_id)
        course_name = course.name if course else ""

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title = QLabel(assignment.title)
        title.setStyleSheet(f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 700; font-size: 10.5pt; background: transparent;")
        text_col.addWidget(title)

        sub = QLabel(course_name)
        sub.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;")
        text_col.addWidget(sub)
        lay.addLayout(text_col, stretch=1)

        delta = assignment.deadline - datetime.now()
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            time_text, color = f"{self._to_fa(days)} روز", _c('PRIMARY', '#2AA6A3')
        elif hours > 0:
            time_text, color = f"{self._to_fa(hours)} ساعت", _c('WARNING', '#FF9500')
        else:
            time_text, color = "کمتر از ۱ ساعت", _c('ERROR', '#FF3B30')

        time_lbl = QLabel(time_text)
        time_lbl.setStyleSheet(f"color: {color}; font-weight: 800; font-size: 10pt; background: transparent;")
        lay.addWidget(time_lbl)

        is_dark = CurrentTheme.is_dark()
        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        frame.setStyleSheet(f"""
                QFrame#CourseCard {{
                    background-color: {card_bg};
                    border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                    border-radius: 12px;
                }}
                QFrame#CourseCard:hover {{
                    background-color: {card_hover};
                    border-color: {color}50;
                }}
            """)
        return frame

    def _set_stat(self, key: str, value: int) -> None:
        if key in self._stat_widgets:
            self._stat_widgets[key].value_label.setText(self._to_fa(value))

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    @staticmethod
    def _to_fa(n: int) -> str:
        fa = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa[int(d)] for d in str(n))