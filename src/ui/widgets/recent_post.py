"""Recent Post: کارت compact برای پست‌های اخیر — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.models.post import Post
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class RecentPost(QFrame):
    """کارت compact پست با آواتار گرادیانتی."""

    clicked = Signal(str)

    def __init__(self, post: Post, course_name: str = "", parent=None) -> None:
        super().__init__(parent)
        self._post = post
        self._course_name = course_name
        self.setObjectName("PostCard")
        self.setFixedHeight(92)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        # --- آواتار گرادیانتی ---
        author_name = self._post.author or "کاربر"
        initial = author_name[0] if author_name else "?"
        avatar = QLabel(initial)
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {_c('PRIMARY', '#2AA6A3')}, stop:1 {_c('PRIMARY_DARK', '#1E807E')});
                color: #FFFFFF; border-radius: 20px; font-size: 13pt; font-weight: 800;
            }}
        """)
        lay.addWidget(avatar)

        # --- محتوا ---
        content = QVBoxLayout()
        content.setSpacing(4)

        # هدر: نویسنده + درس + تاریخ
        header = QHBoxLayout()
        header.setSpacing(8)

        author = QLabel(author_name)
        author.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 700; "
            "font-size: 9.5pt; background: transparent;"
        )
        header.addWidget(author)

        if self._course_name:
            course = QLabel(f"· {self._course_name}")
            course.setStyleSheet(
                f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;"
            )
            header.addWidget(course)

        header.addStretch()

        date = QLabel(self._post.posted_at_jalali or "—")
        date.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8pt; background: transparent;"
        )
        header.addWidget(date)
        content.addLayout(header)

        # متن کوتاه
        text = self._post.text
        if len(text) > 100:
            text = text[:97] + "..."
        body = QLabel(text)
        body.setWordWrap(True)
        body.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; font-size: 9pt; background: transparent;"
        )
        content.addWidget(body)

        lay.addLayout(content, stretch=1)

        # افکت hover
        self.setStyleSheet(f"""
            QFrame#PostCard {{
                background-color: {_c('GLASS_BG', 'rgba(255,255,255,0.68)')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 12px;
            }}
            QFrame#PostCard:hover {{
                background-color: {_c('GLASS_BG_HOVER', 'rgba(255,255,255,0.85)')};
                border-color: {_c('GLASS_BORDER_HOVER', 'rgba(42,166,163,0.35)')};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._post.course_id)
        super().mousePressEvent(event)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._build()