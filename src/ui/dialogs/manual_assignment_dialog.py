"""دیالوگ افزودن تکلیف دستی.

برای تکالیفی که استاد در LMS یا کوئرا ثبت نمی‌کند و سر کلاس تحویل می‌گیرد.
تاریخ/ساعت ورودی به شمسی (جلالی) گرفته شده و به میلادی تبدیل می‌شود.
"""

from __future__ import annotations

from datetime import datetime

import jdatetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.models.assignment import Assignment
from src.models.quera_assignment import QueraAssignment
from src.ui.theme import CurrentTheme


class ManualAssignmentDialog(QDialog):
    """فرم افزودن تکلیف دستی (LMS یا کوئرا)."""

    JALALI_MONTHS = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]

    def __init__(
        self,
        courses: list[tuple[str, str]],
        parent: QWidget | None = None,
    ) -> None:
        """
        Args:
            courses: لیست (course_id, course_name) برای انتخاب درس.
                     برای تکلیف کوئرا، course_id نام درس است.
        """
        super().__init__(parent)
        self.setWindowTitle("➕ افزودن تکلیف دستی")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._courses = courses

        self._build()

    # ============================================================
    # UI
    # ============================================================

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("➕  افزودن تکلیف دستی")
        title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-size: 15pt; font-weight: 800; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(title)

        subtitle = QLabel("مناسب تکالیفی که استاد سر کلاس تحویل می‌گیرد")
        subtitle.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9.5pt; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # === منبع ===
        self.source_combo = QComboBox()
        self.source_combo.addItem("🎓 LMS (تحویل سر کلاس)", "lms")
        self.source_combo.addItem("🎯 کوئرا (تمرین دستی)", "quera")
        self.source_combo.setMinimumHeight(36)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        form.addRow("منبع:", self._wrap(self.source_combo))

        # === درس ===
        self.course_combo = QComboBox()
        self.course_combo.setEditable(True)
        self.course_combo.setMinimumHeight(36)
        self._fill_courses()
        form.addRow("درس:", self._wrap(self.course_combo))

        # === عنوان ===
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("مثلاً: تمرین ۳ — گراف")
        self.title_input.setMinimumHeight(36)
        self.title_input.setAlignment(Qt.AlignRight)
        form.addRow("عنوان:", self._wrap(self.title_input))

        # === توضیحات (اختیاری) ===
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("اختیاری — مثلاً: تحویل دست‌نویس سر کلاس")
        self.desc_input.setMinimumHeight(36)
        self.desc_input.setAlignment(Qt.AlignRight)
        form.addRow("توضیحات:", self._wrap(self.desc_input))

        # === مهلت (تاریخ شمسی) ===
        today = jdatetime.date.today()

        date_row = QHBoxLayout()
        date_row.setSpacing(6)

        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.setValue(today.day)
        self.day_spin.setMinimumHeight(36)

        self.month_combo = QComboBox()
        self.month_combo.addItems(self.JALALI_MONTHS)
        self.month_combo.setCurrentIndex(today.month - 1)
        self.month_combo.setMinimumHeight(36)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(1380, 1500)
        self.year_spin.setValue(today.year)
        self.year_spin.setMinimumHeight(36)

        date_row.addWidget(self.day_spin)
        date_row.addWidget(self.month_combo)
        date_row.addWidget(self.year_spin)

        date_w = QWidget()
        date_w.setLayout(date_row)
        form.addRow("مهلت:", self._wrap(date_w))

        # === ساعت ===
        time_row = QHBoxLayout()
        time_row.setSpacing(6)

        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(23)
        self.hour_spin.setMinimumHeight(36)

        colon = QLabel(":")
        colon.setStyleSheet(f"color: {c.TEXT_PRIMARY}; font-weight: 700; background: transparent;")

        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(59)
        self.minute_spin.setMinimumHeight(36)

        time_hint = QLabel("(پیش‌فرض ۲۳:۵۹)")
        time_hint.setStyleSheet(f"color: {c.TEXT_MUTED}; font-size: 8.5pt; background: transparent;")

        time_row.addWidget(self.hour_spin)
        time_row.addWidget(colon)
        time_row.addWidget(self.minute_spin)
        time_row.addWidget(time_hint)
        time_row.addStretch()

        time_w = QWidget()
        time_w.setLayout(time_row)
        form.addRow("ساعت:", self._wrap(time_w))

        # === حذف تاریخ (تکلیف بدون مهلت مشخص) ===
        self.no_deadline_check = QPushButton("☐  بدون مهلت زمانی (تاریخ ندارم)")
        self.no_deadline_check.setCheckable(True)
        self.no_deadline_check.setCursor(Qt.PointingHandCursor)
        self.no_deadline_check.setStyleSheet("QPushButton { border: none; text-align: right; }")
        self.no_deadline_check.toggled.connect(self._on_no_deadline_toggled)
        form.addRow("", self._wrap(self.no_deadline_check))

        layout.addLayout(form)

        # === دکمه‌ها ===
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("✔  ذخیره تکلیف")
        ok_btn.setObjectName("PrimaryButton")
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("انصراف")
        cancel_btn.setObjectName("SecondaryButton")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _wrap(widget: QWidget) -> QWidget:
        wrapper = QWidget()
        lay = QHBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget)
        return wrapper

    def _fill_courses(self) -> None:
        self.course_combo.clear()
        for cid, name in self._courses:
            self.course_combo.addItem(name, cid)

    def _on_source_changed(self) -> None:
        # هر دو حالت از لیست دروس موجود استفاده می‌کنند؛
        # اگر کاربر قبلاً درس دلخواه تایپ کرده، دست نخورَد.
        line = self.course_combo.lineEdit()
        typed = line.text().strip() if line else ""
        self._fill_courses()
        if typed:
            line.setText(typed)

    def _on_no_deadline_toggled(self, checked: bool) -> None:
        for w in (self.day_spin, self.month_combo, self.year_spin,
                  self.hour_spin, self.minute_spin):
            w.setEnabled(not checked)
        if checked:
            self.no_deadline_check.setText("☑  بدون مهلت زمانی (تاریخ ندارم)")
        else:
            self.no_deadline_check.setText("☐  بدون مهلت زمانی (تاریخ ندارم)")

    # ============================================================
    # Output
    # ============================================================

    def _selected_course(self) -> tuple[str, str]:
        idx = self.course_combo.currentIndex()
        data = self.course_combo.itemData(idx) if idx >= 0 else None
        text = self.course_combo.currentText().strip()
        if data and text == self.course_combo.itemText(idx):
            return str(data), text
        # مقدار تایپ‌شده آزاد → هم id و هم name همان متن است
        return text, text

    def get_assignment(self) -> Assignment | QueraAssignment | None:
        """ساخت مدل تکلیف از مقادیر فرم. None اگر نامعتبر باشد."""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "خطا", "عنوان تکلیف نمی‌تواند خالی باشد.")
            return None

        cid, cname = self._selected_course()
        if not cid:
            QMessageBox.warning(self, "خطا", "نام درس را وارد یا انتخاب کنید.")
            return None

        deadline: datetime | None = None
        deadline_jalali: str | None = None
        if not self.no_deadline_check.isChecked():
            try:
                jdt = jdatetime.datetime(
                    self.year_spin.value(),
                    self.month_combo.currentIndex() + 1,
                    min(self.day_spin.value(), 31),
                    self.hour_spin.value(),
                    self.minute_spin.value(),
                )
                deadline = jdt.togregorian()
            except ValueError:
                QMessageBox.warning(
                    self, "خطا", "تاریخ واردشده معتبر نیست (روز ماه را بررسی کنید)."
                )
                return None
            deadline_jalali = (
                f"{self.day_spin.value()} {self.month_combo.currentText()} "
                f"{self.year_spin.value()} - "
                f"{self.hour_spin.value()}:{self.minute_spin.value():02d}"
            )

        source = self.source_combo.currentData()
        now = datetime.now()

        if source == "quera":
            return QueraAssignment(
                id=f"manual-{int(now.timestamp() * 1000)}",
                name=title,
                course_name=cname,
                finish_time=deadline,
                is_manual=True,
                first_seen_at=now,
                last_seen_at=now,
            )

        return Assignment(
            id=f"manual-{int(now.timestamp() * 1000)}",
            course_id=cid,
            title=title,
            description=self.desc_input.text().strip(),
            deadline=deadline,
            deadline_jalali=deadline_jalali,
            start_at=now,
            start_at_jalali=None,
            is_manual=True,
            first_seen_at=now,
            last_seen_at=now,
        )

    def _on_accept(self) -> None:
        if self.get_assignment() is not None:
            self.accept()
