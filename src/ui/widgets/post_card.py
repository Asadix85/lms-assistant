"""Post Card: کارت نمایش یک پیام wall."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

from src.models.post import Post
from src.ui.theme import Colors


class PostCard(QFrame):
    """کارت نمایش یک پیام wall."""

    def __init__(self, post: Post, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._post = post
        self.setObjectName("PostCard")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(8)

        # === Header Row (author + date) ===
        header = QHBoxLayout()
        header.setSpacing(10)

        author = QLabel(f"👤  {self._post.author}")
        author.setObjectName("PostAuthor")
        author.setAlignment(Qt.AlignRight)
        header.addWidget(author, stretch=1)

        # تاریخ شمسی
        date_text = self._post.posted_at_jalali or "—"
        date = QLabel(date_text)
        date.setObjectName("PostDate")
        date.setAlignment(Qt.AlignLeft)
        header.addWidget(date)

        layout.addLayout(header)

        # === Body ===
        text = QLabel(self._post.text)
        text.setObjectName("PostText")
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignRight)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)

        # === Attachments (اگر بودند) ===
        # TODO: در نسخه بعدی