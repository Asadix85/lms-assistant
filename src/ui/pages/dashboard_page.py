"""Dashboard Page: صفحه اصلی."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt

from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors


class StatCard(QFrame):
    """کارت آماری."""

    def __init__(self, value: str, label: str, icon: str = "📊") -> None:
        super().__init__()
        self.setObjectName("StatCard")
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28pt;")
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
        super().__init__(
            title="داشبورد",
            subtitle="نمای کلی از وضعیت LMS شما",
            parent=parent,
        )
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

        # === Last Sync Info ===
        self.sync_info = QLabel("—")
        self.sync_info.setObjectName("PageSubtitle")
        self.sync_info.setAlignment(Qt.AlignRight)
        self.content_layout.addWidget(self.sync_info)

    def refresh(self) -> None:
        """بارخوانی آمار."""
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
            self.sync_info.setText(f"خطا: {e}")

    @staticmethod
    def _to_fa(n: int) -> str:
        """تبدیل عدد به فارسی."""
        fa_digits = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa_digits[int(d)] for d in str(n))

    def update_from_result(self, result: SyncResult) -> None:
        """به‌روزرسانی از نتیجه Sync."""
        self.refresh()