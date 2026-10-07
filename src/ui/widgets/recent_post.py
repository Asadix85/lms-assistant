"""Recent Post: کارت compact برای پست‌های اخیر."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from src.models.post import Post
from src.ui.theme import CurrentTheme


class RecentPost(QFrame):
    """کارت compact پست."""

    clicked = Signal(str)  # course_id

    def __init__(
        self,
        post: Post,
        course_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._post = post
        self._course_name = course_name

        self.setObjectName("PostCard")
        self.setFixedHeight(88)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # === آواتار (دایره) ===
        avatar = QLabel("👤")
        avatar.setStyleSheet(
            f"background-color: {c.PRIMARY_LIGHT}; "
            "border-radius: 20px; "
            "font-size: 16pt; "
            "border: none;"
        )
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        layout.addWidget(avatar)

        # === متن ===
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        # row: author + course + date
        header = QHBoxLayout()
        header.setSpacing(8)

        author = QLabel(self._post.author)
        author.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 600; font-size: 10pt; "
            "background: transparent;"
        )
        author.setAlignment(Qt.AlignRight)
        header.addWidget(author)

        course_label = QLabel(f"· {self._course_name}")
        course_label.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; background: transparent;"
        )
        header.addWidget(course_label)

        header.addStretch()

        date = QLabel(self._post.posted_at_jalali or "—")
        date.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; background: transparent;"
        )
        date.setAlignment(Qt.AlignLeft)
        header.addWidget(date)

        text_col.addLayout(header)

        # متن کوتاه
        text = self._post.text
        if len(text) > 120:
            text = text[:117] + "..."

        body = QLabel(text)
        body.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignRight)
        text_col.addWidget(body)

        layout.addLayout(text_col, stretch=1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._post.course_id)
        super().mousePressEvent(event)