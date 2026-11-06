"""Quera Page: تمرین‌ها و کلاس‌های کوئرا."""

from __future__ import annotations

from datetime import datetime, timezone

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.quera_assignment import QueraAssignment
from src.storage.database import Database
from src.storage.repositories import QueraAssignmentRepository, QueraCourseRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.empty_state import EmptyState
from src.ui.widgets.quera_assignment_card import QueraAssignmentCard
from src.ui.widgets.quera_course_card import QueraCourseCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class QueraPage(BasePage):
    """صفحه‌ی اختصاصی کوئرا."""

    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._assignments: list[QueraAssignment] = []
        self._filter = "open"
        super().__init__(
            title="کوئرا",
            subtitle="تمرین‌ها و کلاس‌های کوئرا",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        toolbar = QFrame()
        toolbar.setObjectName("Card")
        toolbar.setFixedHeight(60)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(15, 10, 15, 10)
        tb.setSpacing(8)

        self._filter_btns: dict[str, QPushButton] = {}
        for key, label in (
            ("open", "باز"),
            ("done", "انجام‌شده"),
            ("all", "همه"),
            ("overdue", "گذشته"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(72)
            btn.clicked.connect(lambda checked=False, k=key: self._set_filter(k))
            if key == "open":
                btn.setChecked(True)
            self._filter_btns[key] = btn
            tb.addWidget(btn)

        tb.addStretch()

        sync_btn = QPushButton("🔄 همگام‌سازی کوئرا")
        sync_btn.setObjectName("PrimaryButton")
        sync_btn.setFixedHeight(36)
        sync_btn.clicked.connect(self.sync_requested.emit)
        tb.addWidget(sync_btn)

        self.content_layout.addWidget(toolbar)

        self.counter = QLabel("")
        self.counter.setObjectName("PageSubtitle")
        self.counter.setAlignment(Qt.AlignRight)
        self.counter.setContentsMargins(0, 8, 12, 0)
        self.content_layout.addWidget(self.counter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(8, 8, 8, 20)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def _set_filter(self, key: str) -> None:
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        self._render()

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._assignments = QueraAssignmentRepository(db).get_all()
                self._courses = QueraCourseRepository(db).get_all()
        except Exception as e:
            self.counter.setText(f"خطا: {e}")
            self._courses = []
            return
        self._render()

    def _filtered(self) -> list[QueraAssignment]:
        now = datetime.now(timezone.utc)
        items = list(self._assignments)
        if self._filter == "done":
            return [a for a in items if a.is_done]
        if self._filter == "open":
            return [a for a in items if not a.is_done]
        if self._filter == "overdue":
            out = []
            for a in items:
                if a.is_done:
                    continue
                if a.finish_time and a.finish_time.replace(tzinfo=a.finish_time.tzinfo or timezone.utc) < now:
                    out.append(a)
            return out
        return items

    def _render(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # بخش کلاس‌ها (اگر باشد)
        courses = getattr(self, "_courses", []) or []
        if courses and self._filter == "open":
            head = QLabel(f"کلاس‌های کوئرا · {len(courses)}")
            head.setObjectName("SectionTitle")
            self.list_layout.addWidget(head)
            for course in courses:
                try:
                    self.list_layout.addWidget(QueraCourseCard(course))
                except Exception:
                    # اگر کارت با مدل ناسازگار بود، ساده نشان بده
                    lbl = QLabel(getattr(course, "name", str(course)))
                    lbl.setObjectName("CardTitle")
                    self.list_layout.addWidget(lbl)

        items = self._filtered()
        self.counter.setText(
            f"{len(items)} تمرین"
            + (f" · {len(courses)} کلاس" if courses else "")
        )

        head2 = QLabel("تمرین‌ها")
        head2.setObjectName("SectionTitle")
        self.list_layout.addWidget(head2)

        if not items and not courses:
            empty = EmptyState(
                icon_name="star",
                title="تمرین کوئرایی نیست",
                description="اگر حساب کوئرا را در تنظیمات وارد کرده‌اید، همگام‌سازی را بزنید.",
                action_text="همگام‌سازی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)
            self.list_layout.addWidget(empty)
            return

        if not items:
            tip = QLabel("تمرینی با این فیلتر پیدا نشد.")
            tip.setStyleSheet(
                f"color: {_c('TEXT_MUTED', '#8E8E93')}; padding: 12px; background: transparent;"
            )
            tip.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(tip)
        else:
            # مرتب‌سازی: نزدیک‌ترین مهلت اول
            def sort_key(a: QueraAssignment):
                if a.finish_time is None:
                    return datetime.max.replace(tzinfo=timezone.utc)
                ft = a.finish_time
                if ft.tzinfo is None:
                    ft = ft.replace(tzinfo=timezone.utc)
                return ft

            for a in sorted(items, key=sort_key):
                card = QueraAssignmentCard(a)
                card.done_toggled.connect(self._on_done)
                card.deleted.connect(self._on_delete)
                self.list_layout.addWidget(card)

        self.list_layout.addStretch()

    def _on_done(self, aid: str, done: bool) -> None:
        try:
            with Database(self.db_path) as db:
                QueraAssignmentRepository(db).set_done(aid, done)
        except Exception:
            pass
        self.refresh()

    def _on_delete(self, aid: str) -> None:
        try:
            with Database(self.db_path) as db:
                QueraAssignmentRepository(db).delete(aid)
        except Exception:
            pass
        self.refresh()

    def refresh_theme(self) -> None:
        super().refresh_theme()
        self._render()
