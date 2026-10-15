"""Dashboard Page: صفحه اصلی — نسخه‌ی بازطراحی‌شده (خفن!)."""

from __future__ import annotations

from datetime import datetime, timedelta

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

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    PostRepository,
    QueraAssignmentRepository,
    SettingRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.dashboard_stat import DashboardStat
from src.ui.widgets.recent_post import RecentPost
from src.ui.widgets.timeline import HorizontalTimeline
from src.ui.widgets.upcoming_card import UpcomingCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class SectionTitle(QLabel):
    """عنوان بخش با آیکون و خط زیرین."""

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


class DashboardPage(BasePage):
    """صفحه داشبورد — طراحی مدرن با انیمیشن."""

    course_selected = Signal(str)

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._stats: dict[str, DashboardStat] = {}
        self.timeline: HorizontalTimeline | None = None
        self.sync_info: QLabel | None = None
        self._anims: list = []
        self._first_load = True

        super().__init__(
            title="داشبورد",
            subtitle="نمای کلی از وضعیت LMS شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        # === اسکرول ===
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
        # بخش ۱: آمار سریع
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📊  آمار سریع"))

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._stats["courses"] = DashboardStat("📚", "", "درس فعال", "primary")
        self._stats["assignments"] = DashboardStat("📋", "۰", "تکلیف در انتظار", "warning")
        self._stats["events"] = DashboardStat("📅", "", "رویداد هفته", "info")
        self._stats["posts"] = DashboardStat("📢", "۰", "پست هفته", "success")

        for card in self._stats.values():
            stats_row.addWidget(card)
        self.scroll_layout.addLayout(stats_row)

        # ============================================
        # بخش ۲: رویدادهای نزدیک
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("⏰  رویدادهای نزدیک"))

        self.upcoming_container = QVBoxLayout()
        self.upcoming_container.setSpacing(10)
        self.scroll_layout.addLayout(self.upcoming_container)

        # ============================================
        # بخش ۳: پست‌های اخیر
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📢  پست‌های اخیر"))

        self.posts_container = QVBoxLayout()
        self.posts_container.setSpacing(10)
        self.scroll_layout.addLayout(self.posts_container)

        # ============================================
        # بخش ۴: Timeline هفته
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📅  هفته‌ی جاری"))

        self.timeline = HorizontalTimeline()
        self.scroll_layout.addWidget(self.timeline)

        # ============================================
        # بخش ۵: آخرین Sync
        # ============================================
        self.sync_info = QLabel("—")
        self.sync_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sync_info.setStyleSheet(f"""
            color: {_c('TEXT_MUTED', '#8E8E93')};
            font-size: 9.5pt;
            padding: 12px 4px;
            background: transparent;
        """)
        self.scroll_layout.addWidget(self.sync_info)

        self.scroll_layout.addStretch()

    def _fix_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)
        for obj in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj)
            if lbl:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def refresh(self) -> None:
        if not self._stats:
            return

        try:
            with Database(self.db_path) as db:
                self._load_stats(db)
                self._load_upcoming(db)
                self._load_posts(db)
                self._load_sync_info(db)
        except Exception as e:
            print(f"❌ خطا در dashboard: {e}")
            import traceback
            traceback.print_exc()

        self._load_timeline_items()

        # انیمیشن فقط یک بار
        if self._first_load:
            self._fade_in_sections()
            self._first_load = False

    def _fade_in_sections(self) -> None:
        """انیمیشن fade پلکانی برای بخش‌ها."""
        self._anims.clear()
        widgets = []
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                widgets.append(item.widget())
            elif item.layout():
                # برای layout ها، ویجت‌های داخلش رو پیدا کن
                for j in range(item.layout().count()):
                    sub_item = item.layout().itemAt(j)
                    if sub_item.widget():
                        widgets.append(sub_item.widget())

        for i, w in enumerate(widgets[:20]):
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda widget=w: (widget.setGraphicsEffect(None), widget.update()))
            self._anims.append(anim)
            QTimer.singleShot(i * 60, anim.start)

    # ============================================================
    # بخش ۱: آمار
    # ============================================================

    def _load_stats(self, db) -> None:
        from src.utils.quera_adapter import quera_to_assignment

        courses = CourseRepository(db).get_all()
        active_courses = [c for c in courses if c.is_active]

        now = datetime.now()
        lms = AssignmentRepository(db).get_all()
        quera = QueraAssignmentRepository(db).get_all()
        quera_as_assignments = [quera_to_assignment(q) for q in quera]
        assignments = lms + quera_as_assignments

        pending_assignments = [a for a in assignments if not a.deadline or a.deadline >= now]

        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        events = EventRepository(db).get_all()
        week_events = [e for e in events if e.start_at and week_start <= e.start_at < week_end]

        posts = PostRepository(db).get_all()
        week_posts = [p for p in posts if p.posted_at and week_start <= p.posted_at < week_end]

        self._stats["courses"].set_value(self._to_fa(len(active_courses)))
        self._stats["assignments"].set_value(self._to_fa(len(pending_assignments)))
        self._stats["events"].set_value(self._to_fa(len(week_events)))
        self._stats["posts"].set_value(self._to_fa(len(week_posts)))

    # ============================================================
    # بخش ۲: رویدادهای نزدیک
    # ============================================================

    def _load_upcoming(self, db) -> None:
        from src.utils.quera_adapter import quera_to_assignment, quera_course_label, is_quera_item

        self._clear_layout(self.upcoming_container)

        now = datetime.now()
        week_later = now + timedelta(days=7)

        events = EventRepository(db).get_all()
        upcoming_events = [e for e in events if e.start_at and now <= e.start_at <= week_later]

        lms_assignments = AssignmentRepository(db).get_all()
        quera_assignments = QueraAssignmentRepository(db).get_all()
        quera_as_assignments = [quera_to_assignment(q) for q in quera_assignments]
        all_assignments = lms_assignments + quera_as_assignments
        upcoming_assignments = [a for a in all_assignments if a.deadline and now <= a.deadline <= week_later]

        items = []
        for e in upcoming_events:
            items.append((e.start_at, "event", e))
        for a in upcoming_assignments:
            items.append((a.deadline, "assignment", a))

        items.sort(key=lambda x: x[0])
        items = items[:5]

        if not items:
            empty = self._make_empty_upcoming()
            self.upcoming_container.addWidget(empty)
            return

        courses = CourseRepository(db).get_all()
        course_map = {c.id: c.name for c in courses}

        for _, item_type, item in items:
            if is_quera_item(item):
                course_name = quera_course_label(item.course_id)
            else:
                course_name = course_map.get(item.course_id or "", "")

            card = UpcomingCard(item, item_type, course_name)
            card.clicked.connect(self.course_selected.emit)
            self.upcoming_container.addWidget(card)

    def _make_empty_upcoming(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(0, 20, 0, 20)

        icon = QLabel("📅")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 32pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;")
        lay.addWidget(icon)

        text = QLabel("هیچ رویداد یا مهلتی در هفته‌ی جاری نیست")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 10pt; background: transparent;")
        lay.addWidget(text)
        return w

    # ============================================================
    # بخش ۳: پست‌های اخیر
    # ============================================================

    def _load_posts(self, db) -> None:
        self._clear_layout(self.posts_container)

        posts = PostRepository(db).get_all()
        recent = posts[:5]

        if not recent:
            empty = self._make_empty_posts()
            self.posts_container.addWidget(empty)
            return

        courses = CourseRepository(db).get_all()
        course_map = {c.id: c.name for c in courses}

        for post in recent:
            course_name = course_map.get(post.course_id, "")
            card = RecentPost(post, course_name)
            card.clicked.connect(self.course_selected.emit)
            self.posts_container.addWidget(card)

    def _make_empty_posts(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(0, 20, 0, 20)

        icon = QLabel("📢")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 32pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;")
        lay.addWidget(icon)

        text = QLabel("هیچ پستی وجود ندارد")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet(f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 10pt; background: transparent;")
        lay.addWidget(text)
        return w

    # ============================================================
    # بخش ۴: Timeline
    # ============================================================

    def _load_timeline_items(self) -> None:
        if not self.timeline:
            return

        today = jdatetime.date.today()
        week_start = today - timedelta(days=today.weekday())

        items = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            items.append({
                "id": str(i),
                "title": day.strftime("%A"),
                "subtitle": f"{day.day} {self._format_month(day.month)}",
                "active": (day == today),
            })
        self.timeline.set_items(items)

    # ============================================================
    # بخش ۵: Sync info
    # ============================================================

    def _load_sync_info(self, db) -> None:
        settings = SettingRepository(db)
        last_sync = settings.get("last_sync", "—")

        if last_sync and last_sync != "—":
            try:
                dt = datetime.fromisoformat(last_sync)
                jd = jdatetime.datetime.fromgregorian(datetime=dt)
                last_sync = jd.strftime("%Y/%m/%d — %H:%M")
            except Exception:
                last_sync = last_sync[:19].replace("T", " ")

        self.sync_info.setText(f"🔄 آخرین Sync: {last_sync}")

    # ============================================================
    # Helpers
    # ============================================================

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    @staticmethod
    def _format_month(month: int) -> str:
        months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        return months[month]

    @staticmethod
    def _to_fa(n: int) -> str:
        fa = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa[int(d)] for d in str(n))

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        # به‌روزرسانی کارت‌های آماری
        for stat in self._stats.values():
            stat.refresh_theme()

        # به‌روزرسانی upcoming cards
        for i in range(self.upcoming_container.count()):
            item = self.upcoming_container.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'refresh_theme'):
                item.widget().refresh_theme()

        # به‌روزرسانی recent posts
        for i in range(self.posts_container.count()):
            item = self.posts_container.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'refresh_theme'):
                item.widget().refresh_theme()

        # به‌روزرسانی SectionTitle ها
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), SectionTitle):
                item.widget().setStyleSheet(f"""
                    color: {_c('TEXT_PRIMARY', '#1C1C1E')};
                    font-weight: 800;
                    font-size: 13pt;
                    background: transparent;
                    padding: 8px 4px;
                    border-bottom: 2px solid {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.15)')};
                """)