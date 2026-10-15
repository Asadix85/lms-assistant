"""Base Page: کلاس پایه برای همه صفحات."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QBoxLayout,          # ← اضافه شد
)
from PySide6.QtCore import Qt


class BasePage(QWidget):
    """کلاس پایه برای صفحات."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setLayoutDirection(Qt.RightToLeft)

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        # درست شد:
        layout.setDirection(QBoxLayout.TopToBottom)

        # === Page Header ===
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        header_layout.setDirection(QBoxLayout.TopToBottom)

        title_label = QLabel(self._title)
        title_label.setObjectName("PageTitle")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_label.setLayoutDirection(Qt.RightToLeft)
        header_layout.addWidget(title_label)

        if self._subtitle:
            subtitle_label = QLabel(self._subtitle)
            subtitle_label.setObjectName("PageSubtitle")
            subtitle_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            subtitle_label.setLayoutDirection(Qt.RightToLeft)
            header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: rgba(148, 163, 184, 0.2); max-height: 1px;")
        layout.addWidget(sep)

        # === Content ===
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(15)
        self.content_layout.setDirection(QBoxLayout.TopToBottom)
        layout.addLayout(self.content_layout)

        layout.addStretch()

    def refresh(self) -> None:
        """بازخوانی داده‌ها."""
        pass

    def refresh_theme(self) -> None:
        """بعد از تغییر تم، استایل‌ها رو به‌روز کن.

        این متد در کلاس‌های فرزند override می‌شه.
        """
        # به‌روزرسانی separator
        for child in self.findChildren(QFrame):
            if child.frameShape() == QFrame.HLine:
                child.setStyleSheet("background-color: rgba(148, 163, 184, 0.2); max-height: 1px;")

        # به‌روزرسانی title و subtitle
        for obj_name in ("PageTitle", "PageSubtitle"):
            lbl = self.findChild(QLabel, obj_name)
            if lbl:
                # استایل از QSS global میاد، فقط alignment رو دوباره set کن
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)