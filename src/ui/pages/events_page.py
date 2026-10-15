"""Events Page: نمایش رویدادها — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

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

from src.models.event import Event
from src.storage.database import Database
from src.storage.repositories import EventRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.event_card import EventCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class EventsPage(BasePage):
    """صفحه‌ی رویدادها — گروه‌بندی بر اساس روز با هدرهای فارسی."""

    event_selected = Signal(str)

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._all_events: list[Event] = []
        self._filter: str = "all"
        self._first_load = True
        self._anims: list = []

        super().__init__(
            title="رویدادها",
            subtitle="جلسات آنلاین و رویدادهای مهم",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        # === تولبار شیشه‌ای ===
        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        tb = QHBoxLayout(toolbar_card)
        tb.setContentsMargins(14, 10, 14, 10)
        tb.setSpacing(10)

        self.btn_all = self._chip("همه", lambda: self._set_filter("all"), True)
        self.btn_upcoming = self._chip("📅 آینده", lambda: self._set_filter("upcoming"))
        self.btn_today = self._chip("⏰ امروز", lambda: self._set_filter("today"))

        for b in (self.btn_all, self.btn_upcoming, self.btn_today):
            tb.addWidget(b)
        tb.addStretch()

        self.content_layout.addWidget(toolbar_card)

        # === شمارنده ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.counter_label.setContentsMargins(4, 8, 4, 0)
        self.content_layout.addWidget(self.counter_label)

        # === اسکرول ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(4, 8, 4, 24)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def _fix_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)
        for obj in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj)
            if lbl:
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _chip(self, text: str, slot, checked: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("FilterButton")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setFixedHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._all_events = EventRepository(db).get_all()
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

        self.counter_label.setText(
            f"نمایش {len(events)} از {len(self._all_events)} رویداد"
        )

        # پاک کردن
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not events:
            self.list_layout.addWidget(self._make_empty_state())
            return

        # گروه‌بندی بر اساس روز
        groups: dict[str, list[Event]] = defaultdict(list)
        for e in events:
            day = e.start_at.strftime("%Y-%m-%d") if e.start_at else "unknown"
            groups[day].append(e)

        # رندر با انیمیشن
        widgets_to_animate = []
        for day in sorted(groups.keys()):
            day_events = groups[day]

            # هدر روز
            header = self._make_day_header(day, len(day_events))
            self.list_layout.addWidget(header)
            widgets_to_animate.append(header)

            for e in day_events:
                card = EventCard(event_data=e)
                card.join_clicked.connect(self.event_selected.emit)
                self.list_layout.addWidget(card)
                widgets_to_animate.append(card)

        self.list_layout.addStretch()

        # انیمیشن فقط یک بار
        if self._first_load:
            self._fade_in(widgets_to_animate)
            self._first_load = False

    def _make_day_header(self, day: str, count: int) -> QWidget:
        """هدر روز با گرادینت و آیکون."""
        frame = QFrame()
        frame.setObjectName("DayHeader")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)

        icon = QLabel("📅")
        icon.setStyleSheet("font-size: 14pt; background: transparent;")
        lay.addWidget(icon)

        title = QLabel(self._format_day(day))
        title.setStyleSheet(
            f"color: {_c('PRIMARY', '#2AA6A3')}; font-weight: 800; "
            "font-size: 11.5pt; background: transparent;"
        )
        lay.addWidget(title, stretch=1)

        pill = QLabel(f"{count} رویداد")
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedHeight(24)
        pill.setStyleSheet(
            f"color: {_c('PRIMARY', '#2AA6A3')}; "
            f"background-color: {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')}; "
            "border-radius: 12px; padding: 0 12px; font-size: 8.5pt; font-weight: 700;"
        )
        lay.addWidget(pill)

        frame.setStyleSheet(f"""
            QFrame#DayHeader {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')},
                    stop:1 transparent);
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 12px;
            }}
        """)
        return frame

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        icon = QLabel("📅")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"font-size: 44pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;"
        )
        lay.addWidget(icon)

        title = QLabel("هیچ رویدادی نیست")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 13pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        desc = QLabel("برای این فیلتر، رویدادی پیدا نشد.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 10pt; background: transparent;"
        )
        lay.addWidget(desc)
        return w

    def _fade_in(self, widgets: list[QWidget]) -> None:
        """انیمیشن fade با حذف خودکار effect (حل مشکل اسکرول)."""
        self._anims.clear()
        for i, w in enumerate(widgets[:20]):
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(280)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            # حذف effect بعد از پایان
            anim.finished.connect(lambda widget=w: (
                widget.setGraphicsEffect(None),
                widget.update()
            ))

            self._anims.append(anim)
            QTimer.singleShot(i * 30, anim.start)

    def _format_day(self, day: str) -> str:
        if day == "unknown":
            return "بدون تاریخ"
        try:
            import jdatetime
            dt = datetime.strptime(day, "%Y-%m-%d")
            jd = jdatetime.date.fromgregorian(date=dt.date())

            weekdays = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
            months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

            return f"{weekdays[jd.weekday()]} — {jd.day} {months[jd.month]} {jd.year}"
        except Exception:
            return day

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_all.setChecked(f == "all")
        self.btn_upcoming.setChecked(f == "upcoming")
        self.btn_today.setChecked(f == "today")
        self._apply_filters()

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._apply_filters()