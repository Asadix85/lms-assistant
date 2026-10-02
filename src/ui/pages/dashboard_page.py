"""Dashboard Page: صفحه اصلی (با Timeline)."""

import jdatetime
from datetime import timedelta

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors, CurrentTheme
from src.ui.widgets.timeline import HorizontalTimeline


class StatCard(QFrame):
    """کارت آماری."""

    def __init__(self, value: str, label: str, icon: str = "📊") -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        label_widget = QLabel(label)
        label_widget.setObjectName("StatLabel")
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)


class DashboardPage(BasePage):
    """صفحه داشبورد."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._stats: dict[str, StatCard] = {}
        self.timeline: HorizontalTimeline | None = None
        self.sync_info: QLabel | None = None

        super().__init__(
            title="داشبورد",
            subtitle="نمای کلی از وضعیت LMS شما",
            parent=parent,
        )
        # ⚠️ ترتیب درست: _build اول (که در BasePage انجام شده)، بعد refresh
        self.refresh()

    def _build(self) -> None:
        """ساخت ساختار سفارشی."""
        super()._build()

        # === Stat Cards Row ===
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        self._stats["courses"] = StatCard("۰", "درس", "📚")
        self._stats["contents"] = StatCard("۰", "فایل", "📄")
        self._stats["events"] = StatCard("۰", "رویداد", "📅")

        stats_row.addWidget(self._stats["courses"])
        stats_row.addWidget(self._stats["contents"])
        stats_row.addWidget(self._stats["events"])

        self.content_layout.addLayout(stats_row)

        # === Horizontal Timeline ===
        timeline_title = QLabel("📅  هفته‌ی جاری")
        timeline_title.setObjectName("PageSubtitle")
        timeline_title.setAlignment(Qt.AlignRight)
        timeline_title.setStyleSheet(
            "font-weight: bold; font-size: 12pt; padding: 15px 5px 5px 5px; "
            "background: transparent;"
        )
        self.content_layout.addWidget(timeline_title)

        self.timeline = HorizontalTimeline()
        self.content_layout.addWidget(self.timeline)

        # === Last Sync Info ===
        self.sync_info = QLabel("—")
        self.sync_info.setObjectName("PageSubtitle")
        self.sync_info.setAlignment(Qt.AlignRight)
        self.sync_info.setStyleSheet("padding: 15px 5px 0 5px;")
        self.content_layout.addWidget(self.sync_info)

    def refresh(self) -> None:
        """بارخوانی آمار."""
        if not self.sync_info:
            return  # اگر _build هنوز انجام نشده

        try:
            with Database(self.db_path) as db:
                courses_count = CourseRepository(db).count()
                contents_count = ContentRepository(db).count()
                events_count = EventRepository(db).count()

                settings = SettingRepository(db)
                last_sync = settings.get("last_sync_at", "—")
                if last_sync != "—":
                    last_sync = last_sync[:19].replace("T", " ")

            # به‌روزرسانی کارت‌ها
            self._stats["courses"].value_label.setText(self._to_fa(courses_count))
            self._stats["contents"].value_label.setText(self._to_fa(contents_count))
            self._stats["events"].value_label.setText(self._to_fa(events_count))

            self.sync_info.setText(f"🔄 آخرین Sync: {last_sync}")

        except Exception as e:
            if self.sync_info:
                self.sync_info.setText(f"خطا: {e}")

        # بارگذاری timeline
        self._load_timeline_items()

    def _load_timeline_items(self) -> None:
        """بارگذاری آیتم‌های تایم‌لاین (روزهای هفته)."""
        if not self.timeline:
            return

        today = jdatetime.date.today()
        # پیدا کردن شنبه‌ی هفته
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

    @staticmethod
    def _format_month(month: int) -> str:
        months = [
            "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ]
        return months[month]

    @staticmethod
    def _to_fa(n: int) -> str:
        """تبدیل عدد به فارسی."""
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))