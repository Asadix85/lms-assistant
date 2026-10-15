"""Course Stats Cards: کارت‌های آمار درس — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ContentRepository,
    PostRepository,
)
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class CourseStatCard(QFrame):
    """یک کارت آماری با آیکون رنگی و افکت hover."""

    def __init__(
        self,
        icon: str,
        label: str,
        value: str,
        extra: str = "",
        tint: str = "",
        tint_bg: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(128)
        tint = tint or _c("PRIMARY", "#2AA6A3")
        tint_bg = tint_bg or _c("PRIMARY_LIGHT", "rgba(42,166,163,0.12)")

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(7)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {tint_bg}; border-radius: 14px; font-size: 16pt;"
        )
        lay.addWidget(icon_lbl, alignment=Qt.AlignCenter)

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(
            f"color: {tint}; font-weight: 800; font-size: 19pt; background: transparent;"
        )
        value_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(value_lbl)

        label_lbl = QLabel(label)
        label_lbl.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9.5pt; background: transparent;"
        )
        label_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(label_lbl)

        if extra:
            extra_lbl = QLabel(extra)
            extra_lbl.setStyleSheet(
                f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8pt; background: transparent;"
            )
            extra_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(extra_lbl)

        # افکت hover اختصاصی همین کارت
        self.setStyleSheet(f"""
            QFrame#StatCard:hover {{
                background-color: {_c('GLASS_BG_HOVER', 'rgba(255,255,255,0.85)')};
                border: 1px solid {_c('GLASS_BORDER_HOVER', 'rgba(42,166,163,0.35)')};
            }}
        """)


class CourseStatsCards(QWidget):
    """ردیف کارت‌های آمار درس."""

    def __init__(self, db_path: str, course_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self._course_id = course_id
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        try:
            with Database(self._db_path) as db:
                assignments = AssignmentRepository(db).get_by_course(self._course_id)
                contents = ContentRepository(db).get_by_course(self._course_id)
                posts = PostRepository(db).get_by_course(self._course_id, limit=1000)
        except Exception:
            assignments, contents, posts = [], [], []

        now = datetime.now()
        upcoming = sum(1 for a in assignments if a.deadline and a.deadline >= now)
        types = sorted({c_.content_type for c_ in contents})

        lay.addWidget(CourseStatCard(
            icon="📋", label="تکلیف", value=self._to_fa(len(assignments)),
            extra=f"{self._to_fa(upcoming)} فعال" if upcoming else "",
            tint=_c("ACCENT", "#FF9500"), tint_bg="rgba(255, 149, 0, 0.12)",
        ))
        lay.addWidget(CourseStatCard(
            icon="📄", label="فایل", value=self._to_fa(len(contents)),
            extra="، ".join(types[:2]) if types else "",
            tint=_c("PRIMARY", "#2AA6A3"), tint_bg=_c("PRIMARY_LIGHT", "rgba(42,166,163,0.12)"),
        ))
        lay.addWidget(CourseStatCard(
            icon="📢", label="پیام", value=self._to_fa(len(posts)),
            tint=_c("SECONDARY", "#3B8EA5"), tint_bg="rgba(59, 142, 165, 0.12)",
        ))

    @staticmethod
    def _to_fa(n: int) -> str:
        fa = "۰۱۲۳۴۵۶۷۸۹"
        return "".join(fa[int(d)] for d in str(n))