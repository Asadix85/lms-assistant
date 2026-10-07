"""Dashboard Page: صفحه اصلی (بازطراحی‌شده)."""

from datetime import datetime, timedelta

import jdatetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    PostRepository,
    SettingRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.dashboard_stat import DashboardStat
from src.ui.widgets.upcoming_card import UpcomingCard
from src.ui.widgets.recent_post import RecentPost
from src.ui.widgets.timeline import HorizontalTimeline


class SectionTitle(QLabel):
    """عنوان بخش."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("SectionTitle")
        self.setAlignment(Qt.AlignRight)
        self.setFixedHeight(40)


class DashboardPage(BasePage):
    """صفحه داشبورد (نسخه بازطراحی‌شده)."""

    course_selected = Signal(str)

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._stats: dict[str, DashboardStat] = {}
        self.timeline: HorizontalTimeline | None = None
        self.sync_info: QLabel | None = None

        super().__init__(
            title="داشبورد",
            subtitle="نمای کلی از وضعیت LMS شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Scroll ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.scroll_widget)
        self.content_layout.addWidget(scroll, stretch=1)

        # ============================================
        # بخش ۱: آمار سریع (۴ کارت)
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📊  آمار سریع"))

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._stats["courses"] = DashboardStat("📚", "۰", "درس فعال", "primary")
        self._stats["assignments"] = DashboardStat("📋", "۰", "تکلیف در انتظار", "warning")
        self._stats["events"] = DashboardStat("📅", "۰", "رویداد هفته", "info")
        self._stats["posts"] = DashboardStat("📢", "۰", "پست هفته", "success")

        for card in self._stats.values():
            stats_row.addWidget(card)

        self.scroll_layout.addLayout(stats_row)

        # ============================================
        # بخش ۲: رویدادهای نزدیک
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("⏰  رویدادهای نزدیک"))

        self.upcoming_container = QVBoxLayout()
        self.upcoming_container.setSpacing(8)
        self.scroll_layout.addLayout(self.upcoming_container)

        # ============================================
        # بخش ۳: پست‌های اخیر
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📢  پست‌های اخیر"))

        self.posts_container = QVBoxLayout()
        self.posts_container.setSpacing(8)
        self.scroll_layout.addLayout(self.posts_container)

        # ============================================
        # بخش ۴: هفته‌ی جاری (Timeline)
        # ============================================
        self.scroll_layout.addWidget(SectionTitle("📅  هفته‌ی جاری"))

        self.timeline = HorizontalTimeline()
        self.scroll_layout.addWidget(self.timeline)

        # ============================================
        # بخش ۵: آخرین Sync
        # ============================================
        self.sync_info = QLabel("—")
        self.sync_info.setStyleSheet(
            f"color: {CurrentTheme.colors().TEXT_MUTED}; font-size: 10pt; "
            "padding: 16px 4px 4px 4px; background: transparent;"
        )
        self.sync_info.setAlignment(Qt.AlignRight)
        self.scroll_layout.addWidget(self.sync_info)

        self.scroll_layout.addStretch()

    def refresh(self) -> None:
        """بارخوانی داده‌ها."""
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

        # Timeline
        self._load_timeline_items()

    # ============================================================
    # بخش ۱: آمار
    # ============================================================

    def _load_stats(self, db) -> None:
        from src.storage.repositories import QueraAssignmentRepository
        from src.utils.quera_adapter import quera_to_assignment

        courses = CourseRepository(db).get_all()
        active_courses = [c for c in courses if c.is_active]

        now = datetime.now()

        # === LMS + Quera ===
        lms_assignments = AssignmentRepository(db).get_all()
        quera_assignments = QueraAssignmentRepository(db).get_all()

        # تبدیل Quera به Assignment
        all_assignments = list(lms_assignments) + [
            quera_to_assignment(q) for q in quera_assignments
        ]

        # تکالیف در انتظار
        pending_assignments = [
            a for a in all_assignments
            if not a.deadline or a.deadline >= now
        ]

        # رویدادهای هفته‌ی جاری
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        events = EventRepository(db).get_all()
        week_events = [
            e for e in events
            if e.start_at and week_start <= e.start_at < week_end
        ]

        # پست‌های هفته
        posts = PostRepository(db).get_all()
        week_posts = [
            p for p in posts
            if p.posted_at and week_start <= p.posted_at < week_end
        ]

        # آپدیت کارت‌ها
        self._stats["courses"].set_value(self._to_fa(len(active_courses)))
        self._stats["assignments"].set_value(self._to_fa(len(pending_assignments)))
        self._stats["events"].set_value(self._to_fa(len(week_events)))
        self._stats["posts"].set_value(self._to_fa(len(week_posts)))

    # ============================================================
    # بخش ۲: رویدادهای نزدیک
    # ============================================================

    def _load_upcoming(self, db) -> None:
        from src.storage.repositories import QueraAssignmentRepository
        from src.utils.quera_adapter import quera_to_assignment

        # پاک کردن
        self._clear_layout(self.upcoming_container)

        now = datetime.now()
        week_later = now + timedelta(days=7)

        # === رویدادها ===
        events = EventRepository(db).get_all()
        upcoming_events = [
            e for e in events
            if e.start_at and now <= e.start_at <= week_later
        ]

        # === تکالیف LMS ===
        lms_assignments = AssignmentRepository(db).get_all()

        # === تکالیف Quera ===
        quera_assignments = QueraAssignmentRepository(db).get_all()
        quera_as_assignments = [quera_to_assignment(q) for q in quera_assignments]

        all_assignments = lms_assignments + quera_as_assignments

        upcoming_assignments = [
            a for a in all_assignments
            if a.deadline and now <= a.deadline <= week_later
        ]

        # === تکالیف ===
        assignments = AssignmentRepository(db).get_all()
        upcoming_assignments = [
            a for a in assignments
            if a.deadline and now <= a.deadline <= week_later
        ]

        # === ترکیب و مرتب‌سازی ===
        items = []
        for e in upcoming_events:
            items.append((e.start_at, "event", e))
        for a in upcoming_assignments:
            items.append((a.deadline, "assignment", a))

        items.sort(key=lambda x: x[0])
        items = items[:5]  # ۵ تا

        if not items:
            empty = QLabel("هیچ رویداد یا مهلتی در هفته‌ی جاری نیست")
            empty.setStyleSheet(
                f"color: {CurrentTheme.colors().TEXT_MUTED}; "
                "padding: 16px; background: transparent;"
            )
            empty.setAlignment(Qt.AlignCenter)
            self.upcoming_container.addWidget(empty)
            return

        # نام درس‌ها
        courses = CourseRepository(db).get_all()
        course_map = {c.id: c.name for c in courses}

        for _, item_type, item in items:
            course_name = course_map.get(item.course_id or "", "")
            card = UpcomingCard(item, item_type, course_name)
            card.clicked.connect(self.course_selected.emit)
            self.upcoming_container.addWidget(card)

    # ============================================================
    # بخش ۳: پست‌های اخیر
    # ============================================================

    def _load_posts(self, db) -> None:
        self._clear_layout(self.posts_container)

        posts = PostRepository(db).get_all()
        # ۵ پست آخر
        recent = posts[:5]

        if not recent:
            empty = QLabel("هیچ پستی وجود ندارد")
            empty.setStyleSheet(
                f"color: {CurrentTheme.colors().TEXT_MUTED}; "
                "padding: 16px; background: transparent;"
            )
            empty.setAlignment(Qt.AlignCenter)
            self.posts_container.addWidget(empty)
            return

        courses = CourseRepository(db).get_all()
        course_map = {c.id: c.name for c in courses}

        for post in recent:
            course_name = course_map.get(post.course_id, "")
            card = RecentPost(post, course_name)
            card.clicked.connect(self.course_selected.emit)
            self.posts_container.addWidget(card)

    # ============================================================
    # بخش ۴: Timeline
    # ============================================================

    def _load_timeline_items(self) -> None:
        if not self.timeline:
            return

        today = jdatetime.date.today()
        offset = today.weekday()
        week_start = today - timedelta(days=offset)

        items = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            is_today = (day == today)

            items.append({
                "id": str(i),
                "title": day.strftime("%A"),
                "subtitle": f"{day.day} {self._format_month(day.month)}",
                "active": is_today,
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
        months = [
            "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        return months[month]

    @staticmethod
    def _to_fa(n: int) -> str:
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))