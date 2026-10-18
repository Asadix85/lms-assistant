"""Quera Assignment Card: کارت نمایش یک تمرین Quera — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QGraphicsOpacityEffect,
    QMessageBox,
)

from src.models.quera_assignment import QueraAssignment
from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin
from src.ui.widgets.assignment_card import DoneCheckBox


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class QueraAssignmentCard(RTLWidgetMixin, QFrame):
    """کارت تمرین Quera با نوار پیشرفت و هویت رنگی Accent."""

    done_toggled = Signal(str, bool)
    deleted = Signal(str)

    def __init__(self, assignment: QueraAssignment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("AssignmentCard")
        self.setMinimumHeight(130)
        self._build()

    def _build(self) -> None:
        accent = _c("ACCENT", "#FF9500")
        accent_dark = _c("ACCENT_DARK", "#CC7700")
        muted = _c("TEXT_MUTED", "#8E8E93")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(16)

        # --- باکس زمان با رنگ Accent ---
        time_box = QFrame()
        time_box.setFixedSize(84, 84)
        if self._assignment.is_done:
            box_bg = f"{muted}"
            box_style = f"background-color: {box_bg}; border-radius: 16px;"
        else:
            box_style = f"""
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {accent},
                    stop:1 {accent_dark});
                border-radius: 16px;
            """
        time_box.setStyleSheet(f"QFrame {{ {box_style} }}")
        time_lay = QVBoxLayout(time_box)
        time_lay.setAlignment(Qt.AlignCenter)
        time_lay.setSpacing(2)

        if self._assignment.is_done:
            time_text, sub_text = "✅", "انجام شده"
        else:
            days = self._assignment.days_left
            if days < 0:
                time_text, sub_text = "گذشت", "مهلت تمام شده"
            elif days == 0:
                time_text, sub_text = "امروز", "آخرین فرصت!"
            elif days == 1:
                time_text, sub_text = "۱ روز", "فردا تمام می‌شه"
            else:
                time_text = self._to_fa(days) + " روز"
                sub_text = "مانده"

        time_lbl = QLabel(time_text)
        time_lbl.setStyleSheet("color: #FFFFFF; font-size: 14pt; font-weight: 800; background: transparent;")
        time_lbl.setAlignment(Qt.AlignCenter)
        time_lay.addWidget(time_lbl)

        sub_lbl = QLabel(sub_text)
        sub_lbl.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 7.5pt; background: transparent;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        time_lay.addWidget(sub_lbl)
        lay.addWidget(time_box)

        # --- محتوا ---
        content = QVBoxLayout()
        content.setSpacing(8)

        # عنوان + بج کوئرا/دستی
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title = QLabel(self._assignment.name)
        title.setWordWrap(True)
        if self._assignment.is_done:
            title.setStyleSheet(
                f"color: {muted}; font-size: 12pt; font-weight: 700; "
                "text-decoration: line-through; background: transparent;"
            )
        else:
            title.setStyleSheet(
                f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 12pt; "
                "font-weight: 700; background: transparent;"
            )
        title_row.addWidget(title, stretch=1)

        if self._assignment.is_manual:
            manual_badge = QLabel("✍️ دستی")
            manual_badge.setFixedHeight(24)
            p_color = _c("PRIMARY", "#2AA6A3")
            manual_badge.setStyleSheet(
                f"color: {p_color}; background-color: {p_color}22; "
                "border-radius: 12px; padding: 0 10px; font-size: 8pt; font-weight: 700;"
            )
            title_row.addWidget(manual_badge)

        quera_badge = QLabel("🎯 کوئرا")
        quera_badge.setFixedHeight(24)
        quera_badge.setStyleSheet(
            f"color: {accent}; background-color: {accent}22; "
            "border-radius: 12px; padding: 0 10px; font-size: 8pt; font-weight: 700;"
        )
        title_row.addWidget(quera_badge)
        content.addLayout(title_row)

        # نام درس
        course_lbl = QLabel(f"📚  {self._assignment.course_name}")
        course_lbl.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
        )
        content.addWidget(course_lbl)

        # نوار پیشرفت
        if self._assignment.problems_count > 0:
            progress_row = QHBoxLayout()
            progress_row.setSpacing(10)

            progress_lbl = QLabel("پیشرفت:")
            progress_lbl.setStyleSheet(
                f"color: {muted}; font-size: 8.5pt; background: transparent;"
            )
            progress_row.addWidget(progress_lbl)

            bar = QProgressBar()
            bar.setRange(0, self._assignment.problems_count)
            bar.setValue(self._assignment.submitted_count)
            bar.setFixedHeight(8)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.08)')};
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {accent}, stop:1 {accent_dark});
                    border-radius: 4px;
                }}
            """)
            progress_row.addWidget(bar, stretch=1)

            count_lbl = QLabel(
                f"{self._to_fa(self._assignment.submitted_count)}/{self._to_fa(self._assignment.problems_count)}"
            )
            count_lbl.setStyleSheet(
                f"color: {accent}; font-size: 9pt; font-weight: 700; background: transparent;"
            )
            progress_row.addWidget(count_lbl)
            content.addLayout(progress_row)

        lay.addLayout(content, stretch=1)

        # --- ستون سمت چپ: چک‌باکس «انجام شد» + دکمه‌ها ---
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        self.done_cb = DoneCheckBox("انجام شد")
        self.done_cb.setChecked(self._assignment.is_done)
        self.done_cb.toggled.connect(self._on_done_toggled)
        right_col.addWidget(self.done_cb, alignment=Qt.AlignRight)

        open_btn = QPushButton("باز کردن  ↗")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setMinimumWidth(120)
        open_btn.setFixedHeight(40)
        open_btn.setEnabled(not self._assignment.is_done)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent}, stop:1 {accent_dark});
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 10pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {accent_dark};
            }}
            QPushButton:disabled {{
                background-color: {muted};
                color: #FFFFFF;
            }}
        """)
        open_btn.clicked.connect(self._on_open)
        right_col.addWidget(open_btn)

        if self._assignment.is_manual:
            del_btn = QPushButton("🗑 حذف")
            del_btn.setObjectName("SecondaryButton")
            del_btn.setToolTip("حذف تمرین دستی")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(self._on_delete)
            right_col.addWidget(del_btn)

        right_col.addStretch()
        lay.addLayout(right_col)

        # --- محو و غیرفعال کل کارت در حالت انجام‌شده ---
        if self._assignment.is_done:
            self.setEnabled(False)
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.6)
            self.setGraphicsEffect(eff)

    def _on_done_toggled(self, checked: bool) -> None:
        self.done_toggled.emit(self._assignment.id, checked)

    def _on_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            "حذف تمرین",
            f"آیا «{self._assignment.name}» حذف شود؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.deleted.emit(self._assignment.id)

    def _on_open(self) -> None:
        url = f"https://quera.org/course/assignments/{self._assignment.id}/problems"
        QDesktopServices.openUrl(QUrl(url))

    @staticmethod
    def _to_fa(n: int) -> str:
        fa = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa[int(d)] for d in str(n))