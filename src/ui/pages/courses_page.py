"""Courses Page: نمایش دروس LMS + کلاس‌های Quera — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.models.course import Course, CourseStatus
from src.models.quera_course import QueraCourse
from src.storage.database import Database
from src.storage.repositories import CourseRepository, QueraCourseRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.course_card import CourseCard
from src.ui.widgets.quera_course_card import QueraCourseCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CoursesPage(BasePage):
    """صفحه‌ی دروس (LMS + Quera) — گرید واکنش‌گرا با تولبار شیشه‌ای."""

    course_selected = Signal(str)
    sync_requested = Signal()

    CARD_MIN_WIDTH = 300

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._lms_courses: list[Course] = []
        self._quera_courses: list[QueraCourse] = []
        self._filter_domain: str | None = None
        self._filter_active: bool = False
        self._search_text: str = ""
        self._cards: list[QWidget] = []
        self._cols: int = 0
        self._anims: list = []
        self._first_load = True

        super().__init__(
            title="دروس",
            subtitle="همه‌ی دروس شما (LMS + Quera)",
            parent=parent,
        )
        self.refresh()

    # --------------------------------------------------------
    #  اسکلت
    # --------------------------------------------------------

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        # === تولبار شیشه‌ای ===
        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        tb = QHBoxLayout(toolbar_card)
        tb.setContentsMargins(14, 10, 14, 10)
        tb.setSpacing(10)

        # -- سرچ‌باکس --
        search_frame = QFrame()
        search_frame.setFixedHeight(44)
        search_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {_c('GLASS_BG', 'rgba(255,255,255,0.68)')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 12px;
            }}
        """)
        sf_lay = QHBoxLayout(search_frame)
        sf_lay.setContentsMargins(14, 0, 10, 0)
        sf_lay.setSpacing(8)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("background: transparent; font-size: 11pt;")
        sf_lay.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجوی نام درس، استاد یا کد درس…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; padding: 0; "
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 10.5pt; }}"
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        sf_lay.addWidget(self.search_input, stretch=1)
        tb.addWidget(search_frame, stretch=1)

        # -- چیپ‌های فیلتر --
        self.btn_all = self._chip("همه", lambda: self._set_filter(None), True)
        self.btn_lms3 = self._chip("🟢 lms3", lambda: self._set_filter("lms3"))
        self.btn_lms4 = self._chip("🔵 lms4", lambda: self._set_filter("lms4"))
        self.btn_quera = self._chip("🎯 کوئرا", lambda: self._set_filter("quera"))
        self.btn_active = self._chip("✓ فعال", self._toggle_active)
        for b in (self.btn_all, self.btn_lms3, self.btn_lms4,
                  self.btn_quera, self.btn_active):
            tb.addWidget(b)

        self.content_layout.addWidget(toolbar_card)

        # === ردیف شمارنده + خلاصه ===
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(4, 8, 4, 0)

        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        meta_row.addWidget(self.counter_label)

        meta_row.addStretch()

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 9pt; background: transparent;"
        )
        meta_row.addWidget(self.summary_label)
        self.content_layout.addLayout(meta_row)

        # === اسکرول + گرید ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.grid_widget = QWidget()
        host_lay = QVBoxLayout(self.grid_widget)
        host_lay.setContentsMargins(4, 8, 4, 24)
        host_lay.setSpacing(0)

        self.cards_host = QWidget()
        self.grid_layout = QGridLayout(self.cards_host)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        for col in range(4):
            self.grid_layout.setColumnStretch(col, 0)
        host_lay.addWidget(self.cards_host)

        self.empty_widget = self._make_empty_state()
        host_lay.addWidget(self.empty_widget)
        host_lay.addStretch()

        scroll.setWidget(self.grid_widget)
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

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        icon = QLabel("🔍")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"font-size: 44pt; background: transparent; color: {_c('TEXT_MUTED', '#8E8E93')};"
        )
        lay.addWidget(icon)

        title = QLabel("هیچ درسی پیدا نشد")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 13pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        desc = QLabel("فیلترها رو تغییر بده یا یک همگام‌سازی جدید بزن.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 10pt; background: transparent;"
        )
        lay.addWidget(desc)

        lay.addSpacing(14)
        btn = QPushButton("🔄  بروزرسانی")
        btn.setObjectName("PrimaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedSize(150, 40)
        btn.clicked.connect(self.sync_requested.emit)
        lay.addWidget(btn, alignment=Qt.AlignCenter)

        w.setVisible(False)
        return w

    # --------------------------------------------------------
    #  داده و فیلتر
    # --------------------------------------------------------

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._lms_courses = CourseRepository(db).get_all()
                self._quera_courses = QueraCourseRepository(db).get_all()
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        lms = list(self._lms_courses)
        quera = list(self._quera_courses)

        if self._filter_domain == "quera":
            lms = []
        elif self._filter_domain:
            quera = []
            lms = [c for c in lms if c.domain == self._filter_domain]

        if self._filter_active:
            lms = [c for c in lms if c.status == CourseStatus.ACTIVE]
            quera = [q for q in quera if q.is_active]

        if self._search_text:
            s = self._search_text.lower()
            lms = [
                c for c in lms
                if s in c.name.lower()
                or s in (c.teacher or "").lower()
                or s in (c.code or "").lower()
            ]
            quera = [
                q for q in quera
                if s in q.name.lower() or s in (q.teacher or "").lower()
            ]

        total = len(lms) + len(quera)
        total_all = len(self._lms_courses) + len(self._quera_courses)
        self.counter_label.setText(f"نمایش {total} از {total_all} درس")
        self.summary_label.setText(
            f"{len(self._lms_courses)} درس LMS  •  {len(self._quera_courses)} کلاس کوئرا"
        )

        # --- پاک کردن کارت‌های قبلی ---
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards = []
        self._cols = 0

        has_items = bool(lms or quera)
        self.cards_host.setVisible(has_items)
        self.empty_widget.setVisible(not has_items)
        if not has_items:
            return

        for c_ in lms:
            card = CourseCard(c_)
            card.clicked.connect(self.course_selected.emit)
            self._cards.append(card)
        for q_ in quera:
            card = QueraCourseCard(q_)
            card.clicked.connect(self._on_quera_course_clicked)
            self._cards.append(card)

        self._relayout_cards(force=True)
        # فقط یک بار انیمیشن
        if self._first_load:
            self._fade_in_cards_simple()
            self._first_load = False

    def _fade_in_cards_simple(self) -> None:
        """انیمیشن ساده فقط برای اولین لود."""
        from PySide6.QtWidgets import QGraphicsOpacityEffect

        self._anims.clear()
        for i, card in enumerate(self._cards[:10]):  # فقط ۱۰ تای اول
            eff = QGraphicsOpacityEffect(card)
            card.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(300)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            # مهم: بعد از پایان انیمیشن، effect رو حذف کن
            anim.finished.connect(lambda c=card: (
                c.setGraphicsEffect(None),  # ← کلید حل مشکل!
                c.update()
            ))

            self._anims.append(anim)
            QTimer.singleShot(i * 40, anim.start)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        # به‌روزرسانی کارت‌ها
        for card in self._cards:
            if hasattr(card, 'refresh_theme'):
                card.refresh_theme()

        # رندر مجدد با تم جدید
        self._apply_filters()

    def _relayout_cards(self, force: bool = False) -> None:
        if not self._cards:
            return
        avail = self.cards_host.width() or self.width()
        cols = max(1, min(4, (avail + 14) // self.CARD_MIN_WIDTH))
        if not force and cols == self._cols:
            return
        self._cols = cols

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        for col in range(4):
            self.grid_layout.setColumnStretch(col, 1 if col < cols else 0)
        for i, w in enumerate(self._cards):
            self.grid_layout.addWidget(w, i // cols, i % cols)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._relayout_cards()

    # --------------------------------------------------------
    #  رویدادها
    # --------------------------------------------------------

    def _on_quera_course_clicked(self, synthetic_id: str) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        quera_id = synthetic_id.replace("quera_", "")
        QDesktopServices.openUrl(QUrl(f"https://quera.org/course/{quera_id}"))

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text
        self._apply_filters()

    def _set_filter(self, domain: str | None) -> None:
        self._filter_domain = domain
        self.btn_all.setChecked(domain is None)
        self.btn_lms3.setChecked(domain == "lms3")
        self.btn_lms4.setChecked(domain == "lms4")
        self.btn_quera.setChecked(domain == "quera")
        self._apply_filters()

    def _toggle_active(self) -> None:
        self._filter_active = self.btn_active.isChecked()
        self._apply_filters()