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
    QFrame, QSizePolicy,
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
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum,  # ← مهم: ارتفاع بر اساس محتوا
        )

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

        # ⚠️ اجبار به به‌روزرسانی layout
        self.list_widget.updateGeometry()
        self.list_widget.adjustSize()

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
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

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

            # Day header (بدون ── که RTL رو خراب می‌کنه)
            header = QLabel(self._format_day(day))
            header.setObjectName("DayHeader")
            header.setAlignment(Qt.AlignCenter)  # ← وسط‌چین
            header.setStyleSheet(
                "background-color: rgba(42, 166, 163, 0.1); "
                "color: #2AA6A3; "
                "font-weight: bold; "
                "font-size: 11pt; "
                "padding: 8px; "
                "border-radius: 8px; "
                "margin: 12px 0 6px 0;"
            )
            self.list_layout.addWidget(header)

            for e in day_events:
                card = EventCard(event_data=e)
                card.join_clicked.connect(self.event_selected.emit)
                self.list_layout.addWidget(card)

        # ⚠️ اضافه کن stretch در انتها
        self.list_layout.addStretch()

    def _format_day(self, day: str) -> str:
        if day == "unknown":
            return "بدون تاریخ"
        try:
            from datetime import datetime as dt_cls
            import jdatetime

            dt = dt_cls.strptime(day, "%Y-%m-%d")
            jd = jdatetime.date.fromgregorian(date=dt.date())

            # نام روز به فارسی
            weekdays = [
                "شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه",
                "چهارشنبه", "پنج‌شنبه", "جمعه",
            ]
            # jdatetime.weekday(): شنبه=0
            day_name = weekdays[jd.weekday()]

            # نام ماه
            months = [
                "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
                "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
            ]
            month_name = months[jd.month]

            return f"{day_name} — {jd.day} {month_name} {jd.year}"

        except Exception as e:
            print(f"خطا در فرمت روز: {e}")
            return day

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_all.setChecked(f == "all")
        self.btn_upcoming.setChecked(f == "upcoming")
        self.btn_today.setChecked(f == "today")
        self._apply_filters()