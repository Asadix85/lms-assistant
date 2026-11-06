"""Map Page: مکان‌های کلاس‌های شما روی نقشه دانشگاه."""

from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.locations import CampusLocation, UI_LOCATIONS, get_location
from src.storage.database import Database
from src.storage.repositories import CourseRepository, CourseScheduleRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.class_location_card import ClassLocationCard
from src.ui.widgets.empty_state import EmptyState


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class MapPage(BasePage):
    """صفحه‌ی نقشه مکان‌های کلاس."""

    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        # key = location keyword matched, value = (CampusLocation|None, raw texts, course names)
        self._entries: list[tuple[str, CampusLocation | None, list[str], list[str]]] = []
        super().__init__(
            title="نقشه مکان‌ها",
            subtitle="ساختمان‌هایی که در آن‌ها کلاس دارید",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        self.counter = QLabel("")
        self.counter.setObjectName("PageSubtitle")
        self.counter.setAlignment(Qt.AlignRight)
        self.counter.setContentsMargins(0, 0, 12, 0)
        self.content_layout.addWidget(self.counter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(14)
        self.list_layout.setContentsMargins(8, 8, 8, 20)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        """استخراج مکان‌های یکتا از برنامه‌ی کلاس‌ها."""
        raw_by_key: dict[str, set[str]] = defaultdict(set)
        courses_by_key: dict[str, set[str]] = defaultdict(set)
        unmatched: dict[str, set[str]] = defaultdict(set)

        try:
            with Database(self.db_path) as db:
                courses = {c.id: c.name for c in CourseRepository(db).get_all()}
                all_schedules = CourseScheduleRepository(db).get_all()
                schedules = [
                    (courses.get(sch.course_id, sch.course_id), sch)
                    for sch in all_schedules
                    if sch.sessions
                ]
        except Exception as e:
            self.counter.setText(f"خطا: {e}")
            return

        for cname, sch in schedules:
            for session in sch.sessions:
                loc_text = (session.location or "").strip()
                if not loc_text:
                    continue
                loc = get_location(loc_text)
                if loc is None:
                    unmatched[loc_text].add(cname)
                    continue
                # کلید پایدار: نام ساختمان
                key = f"{loc.name}|{loc.building}"
                raw_by_key[key].add(loc_text)
                courses_by_key[key].add(cname)

        self._entries = []
        for key, raws in sorted(raw_by_key.items(), key=lambda x: x[0]):
            sample = next(iter(raws))
            loc = get_location(sample)
            self._entries.append(
                (sample, loc, sorted(raws), sorted(courses_by_key[key]))
            )

        # مکان‌های ناشناس
        for raw, cnames in sorted(unmatched.items()):
            self._entries.append((raw, None, [raw], sorted(cnames)))

        self._render()

    def _render(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        n = len(self._entries)
        self.counter.setText(f"{n} مکان" if n else "")

        if not self._entries:
            empty = EmptyState(
                icon_name="graduation-cap",
                title="مکانی ثبت نشده",
                description="بعد از همگام‌سازی دروس، مکان کلاس‌ها از برنامه استخراج می‌شود.",
                action_text="همگام‌سازی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)
            self.list_layout.addWidget(empty)
            return

        for raw_text, loc, raws, course_names in self._entries:
            block = QFrame()
            block.setObjectName("MapCard")
            blay = QVBoxLayout(block)
            blay.setContentsMargins(0, 0, 0, 12)
            blay.setSpacing(8)

            # کارت نقشه / مکان موجود
            card = ClassLocationCard(raw_text)
            blay.addWidget(card)

            if course_names:
                chips = QHBoxLayout()
                chips.setSpacing(6)
                chips.setContentsMargins(12, 0, 12, 0)
                for name in course_names[:6]:
                    chip = QLabel(name)
                    chip.setStyleSheet(
                        f"color: {_c('PRIMARY', '#2AA6A3')}; "
                        f"background: {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')}; "
                        "border-radius: 10px; padding: 4px 10px; font-size: 8.5pt; font-weight: 600;"
                    )
                    chips.addWidget(chip)
                if len(course_names) > 6:
                    more = QLabel(f"+{len(course_names) - 6}")
                    more.setStyleSheet(
                        f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;"
                    )
                    chips.addWidget(more)
                chips.addStretch()
                blay.addLayout(chips)

            self.list_layout.addWidget(block)

        self.list_layout.addStretch()

    def refresh_theme(self) -> None:
        super().refresh_theme()
        self._render()
