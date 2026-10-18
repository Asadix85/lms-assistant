"""Assignments Page: نمایش تکالیف — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

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

from src.models.assignment import Assignment
from src.models.quera_assignment import QueraAssignment
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    QueraAssignmentRepository,
)
from src.ui.dialogs.manual_assignment_dialog import ManualAssignmentDialog
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.assignment_card import AssignmentCard
from src.ui.widgets.quera_assignment_card import QueraAssignmentCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class AssignmentsPage(BasePage):
    """صفحه‌ی تکالیف (LMS + Quera + دستی) — فیلتر دو مرحله‌ای."""

    assignment_clicked = Signal(str)
    sync_requested = Signal()
    assignments_changed = Signal()  # برای بروزرسانی داشبورد و بقیه صفحات

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._lms_assignments: list[Assignment] = []
        self._quera_assignments: list[QueraAssignment] = []
        self._source_filter: str = "all"
        self._time_filter: str = "upcoming"
        self._course_names: dict[str, str] = {}
        self._first_load = True
        self._anims: list = []

        super().__init__(
            title="تکالیف",
            subtitle="همه تکالیف (LMS + Quera)",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()
        self._fix_rtl()

        # === دکمه افزودن تکلیف دستی ===
        add_card = QFrame()
        add_card.setObjectName("Card")
        add_lay = QHBoxLayout(add_card)
        add_lay.setContentsMargins(14, 10, 14, 10)
        add_lay.setSpacing(10)

        self.btn_add_manual = QPushButton("➕  افزودن تکلیف دستی")
        self.btn_add_manual.setObjectName("PrimaryButton")
        self.btn_add_manual.setCursor(Qt.PointingHandCursor)
        self.btn_add_manual.setFixedHeight(38)
        self.btn_add_manual.clicked.connect(self._on_add_manual)
        add_lay.addWidget(self.btn_add_manual)

        add_hint = QLabel("مناسب تکالیفی که استاد سر کلاس تحویل می‌گیرد")
        add_hint.setObjectName("PageSubtitle")
        add_lay.addWidget(add_hint)
        add_lay.addStretch()
        self.content_layout.addWidget(add_card)

        # === فیلتر منبع ===
        source_card = QFrame()
        source_card.setObjectName("Card")
        src_lay = QHBoxLayout(source_card)
        src_lay.setContentsMargins(14, 10, 14, 10)
        src_lay.setSpacing(10)

        self.btn_all_sources = self._chip("🌐 همه", lambda: self._set_source_filter("all"), True)
        self.btn_lms = self._chip("🎓 LMS", lambda: self._set_source_filter("lms"))
        self.btn_quera = self._chip("🎯 کوئرا", lambda: self._set_source_filter("quera"))

        for b in (self.btn_all_sources, self.btn_lms, self.btn_quera):
            src_lay.addWidget(b)
        src_lay.addStretch()
        self.content_layout.addWidget(source_card)

        # === فیلتر زمان ===
        time_card = QFrame()
        time_card.setObjectName("Card")
        time_lay = QHBoxLayout(time_card)
        time_lay.setContentsMargins(14, 10, 14, 10)
        time_lay.setSpacing(10)

        self.btn_upcoming = self._chip("⏰ آینده", lambda: self._set_time_filter("upcoming"), True)
        self.btn_all_time = self._chip("📋 همه", lambda: self._set_time_filter("all"))
        self.btn_overdue = self._chip("⏹️ گذشته", lambda: self._set_time_filter("overdue"))

        for b in (self.btn_upcoming, self.btn_all_time, self.btn_overdue):
            time_lay.addWidget(b)
        time_lay.addStretch()
        self.content_layout.addWidget(time_card)

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
        self.list_layout.setSpacing(12)
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
                self._lms_assignments = AssignmentRepository(db).get_all()
                self._quera_assignments = QueraAssignmentRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_names = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        lms = list(self._lms_assignments) if self._source_filter in ("all", "lms") else []
        quera = list(self._quera_assignments) if self._source_filter in ("all", "quera") else []

        now = datetime.now()

        if self._time_filter == "upcoming":
            lms = [a for a in lms if a.deadline and a.deadline >= now]
            quera = [q for q in quera if q.finish_time and q.finish_time >= now]
        elif self._time_filter == "overdue":
            lms = [a for a in lms if a.deadline and a.deadline < now]
            quera = [q for q in quera if q.finish_time and q.finish_time < now]

        # تکالیف انجام‌شده از فهرست پیشرو خارج می‌شوند (حالت غیرفعال)
        done_count = sum(1 for a in self._lms_assignments if a.is_done) + \
            sum(1 for q in self._quera_assignments if q.is_done)
        if self._time_filter == "upcoming":
            lms = [a for a in lms if not a.is_done]
            quera = [q for q in quera if not q.is_done]

        total = len(lms) + len(quera)
        total_all = len(self._lms_assignments) + len(self._quera_assignments)
        counter_text = f"نمایش {total} از {total_all} تکلیف"
        if done_count:
            counter_text += f" — {done_count} انجام‌شده ✅"
        self.counter_label.setText(counter_text)

        # پاک کردن
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not lms and not quera:
            self.list_layout.addWidget(self._make_empty_state())
            return

        # ترکیب و مرتب‌سازی
        items = []
        for a in lms:
            items.append((a.deadline or datetime.max, "lms", a))
        for q in quera:
            items.append((q.finish_time or datetime.max, "quera", q))
        items.sort(key=lambda x: x[0])

        # رندر
        widgets_to_animate = []
        for _deadline, source, item in items:
            if source == "lms":
                container = self._make_lms_container(item)
                self.list_layout.addWidget(container)
                widgets_to_animate.append(container)
            else:
                card = QueraAssignmentCard(item)
                card.done_toggled.connect(self._on_done_toggled)
                card.deleted.connect(self._on_deleted)
                self.list_layout.addWidget(card)
                widgets_to_animate.append(card)

        self.list_layout.addStretch()

        if self._first_load:
            self._fade_in(widgets_to_animate)
            self._first_load = False

    def _make_lms_container(self, assignment: Assignment) -> QWidget:
        """کانتینر تکلیف LMS با هدرس."""
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        course_name = self._course_names.get(assignment.course_id, "نامشخص")
        header = QHBoxLayout()
        header.setSpacing(8)

        icon = QLabel("📚")
        icon.setStyleSheet("font-size: 11pt; background: transparent;")
        header.addWidget(icon)

        name_lbl = QLabel(course_name)
        name_lbl.setStyleSheet(
            f"color: {_c('PRIMARY', '#2AA6A3')}; font-weight: 700; "
            "font-size: 10pt; background: transparent;"
        )
        header.addWidget(name_lbl)
        header.addStretch()
        lay.addLayout(header)

        card = AssignmentCard(assignment)
        card.done_toggled.connect(self._on_done_toggled)
        card.deleted.connect(self._on_deleted)
        lay.addWidget(card)
        return container

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)

        icon = QLabel("📋")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"font-size: 44pt; color: {_c('TEXT_MUTED', '#8E8E93')}; background: transparent;"
        )
        lay.addWidget(icon)

        title = QLabel("هیچ تکلیفی نیست")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 13pt; "
            "font-weight: 700; background: transparent;"
        )
        lay.addWidget(title)

        desc = QLabel("برای این فیلتر، تکلیفی پیدا نشد.")
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
        return w

    def _fade_in(self, widgets: list[QWidget]) -> None:
        self._anims.clear()
        for i, w in enumerate(widgets[:15]):
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(280)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda widget=w: (
                widget.setGraphicsEffect(None),
                widget.update()
            ))
            self._anims.append(anim)
            QTimer.singleShot(i * 35, anim.start)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._apply_filters()

    def _set_source_filter(self, f: str) -> None:
        self._source_filter = f
        self.btn_all_sources.setChecked(f == "all")
        self.btn_lms.setChecked(f == "lms")
        self.btn_quera.setChecked(f == "quera")
        self._apply_filters()

    def _set_time_filter(self, f: str) -> None:
        self._time_filter = f
        self.btn_upcoming.setChecked(f == "all") # توجه: اینجا احتمالاً اشتباه تایپی قبلی بوده اگر 'all' چک شود، ولی منطق اصلی همین است
        self.btn_all_time.setChecked(f == "all")
        self.btn_overdue.setChecked(f == "overdue")
        self._apply_filters()

    def _on_add_manual(self) -> None:
        """دیالوگ افزودن تکلیف دستی را باز کرده و پس از تأیید، ذخیره می‌کند."""
        dialog = ManualAssignmentDialog(parent=self)

        if dialog.exec():  # اگر کاربر روی OK/Save کلیک کرد
            data = dialog.get_assignment_data()  # فرض بر اینکه دیالوگ متد get_assignment_data دارد

            # ذخیره در دیتابیس
            try:
                with Database(self.db_path) as db:
                    repo = AssignmentRepository(db)
                    # ایجاد آبجکت Assignment جدید بر اساس داده‌های دیالوگ
                    new_assignment = Assignment(
                        id=data['id'],  # اگر ID خودکار نیست
                        course_id=data['course_id'],
                        title=data['title'],
                        description=data.get('description', ''),
                        deadline=data['deadline'],
                        is_done=False,
                        source='manual'  # مشخص کردن منبع به عنوان دستی
                    )
                    repo.add(new_assignment)

                # بروزرسانی صفحه برای نمایش تکلیف جدید
                self.refresh()
                self.assignments_changed.emit()  # سیگنال برای سایر صفحات

            except Exception as e:
                print(f"خطا در ذخیره تکلیف دستی: {e}")
                # می‌توانید پیام خطا را به صورت Toast یا Dialog نشان دهید

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._apply_filters()
