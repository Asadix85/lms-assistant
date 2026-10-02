"""Events Page: نمایش رویدادها (جلسات آنلاین) گروه‌بندی‌شده بر اساس روز."""

from collections import defaultdict
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

from src.models.event import Event
from src.storage.database import Database
from src.storage.repositories import EventRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.event_card import EventCard


class EventsPage(BasePage):
    """صفحه‌ی رویدادها."""

    event_selected = Signal(str)

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._all_events: list[Event] = []
        self._filter: str = "all"
        super().__init__(
            title="رویدادها",
            subtitle="جلسات آنلاین و رویدادهای مهم",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Toolbar ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_all = QPushButton("همه")
        self.btn_all.setObjectName("FilterButton")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self._set_filter("all"))
        toolbar.addWidget(self.btn_all)

        self.btn_upcoming = QPushButton("📅 آینده")
        self.btn_upcoming.setObjectName("FilterButton")
        self.btn_upcoming.setCheckable(True)
        self.btn_upcoming.clicked.connect(lambda: self._set_filter("upcoming"))
        toolbar.addWidget(self.btn_upcoming)

        self.btn_today = QPushButton("⏰ امروز")
        self.btn_today.setObjectName("FilterButton")
        self.btn_today.setCheckable(True)
        self.btn_today.clicked.connect(lambda: self._set_filter("today"))
        toolbar.addWidget(self.btn_today)

        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

        # === Counter ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.content_layout.addWidget(self.counter_label)

        # === Scroll ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                repo = EventRepository(db)
                self._all_events = repo.get_all()
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        events = list(self._all_events)
        now = datetime.now()

        if self._filter == "upcoming":
            events = [e for e in events if e.start_at and e.start_at >= now]
        elif self._filter == "today":
            events = [
                e for e in events
                if e.start_at and e.start_at.date() == now.date()
            ]

        self.counter_label.setText(f"نمایش {len(events)} از {len(self._all_events)} رویداد")

        # پاک کردن
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not events:
            empty = QLabel("هیچ رویدادی با این فیلتر نیست.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty)
            return

        # گروه‌بندی بر اساس روز
        groups: dict = defaultdict(list)
        for e in events:
            if e.start_at:
                day = e.start_at.strftime("%Y-%m-%d")
            else:
                day = "unknown"
            groups[day].append(e)

        # رندر
        for day in sorted(groups.keys()):
            day_events = groups[day]

            # Day header
            header = QLabel(f"──  {self._format_day(day)}  ──")
            header.setObjectName("DayHeader")
            header.setAlignment(Qt.AlignRight)
            self.list_layout.addWidget(header)

            for e in day_events:
                card = EventCard(event_data=e)
                card.join_clicked.connect(self.event_selected.emit)
                self.list_layout.addWidget(card)

    def _format_day(self, day: str) -> str:
        if day == "unknown":
            return "بدون تاریخ"
        try:
            dt = datetime.strptime(day, "%Y-%m-%d")
            return dt.strftime("%A, %d %B %Y")
        except Exception:
            return day

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_all.setChecked(f == "all")
        self.btn_upcoming.setChecked(f == "upcoming")
        self.btn_today.setChecked(f == "today")
        self._apply_filters()