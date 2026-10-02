"""Base Page: کلاس پایه برای همه صفحات."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt


class BasePage(QWidget):
    """کلاس پایه برای صفحات."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle

        # ⚠️ شفافیت
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # === Page Header ===
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)

        title_label = QLabel(self._title)
        title_label.setObjectName("PageTitle")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(title_label)

        if self._subtitle:
            subtitle_label = QLabel(self._subtitle)
            subtitle_label.setObjectName("PageSubtitle")
            subtitle_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #E1E4E8; max-height: 1px;")
        layout.addWidget(sep)

        # === Content ===
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(15)
        layout.addLayout(self.content_layout)

        layout.addStretch()

    def refresh(self) -> None:
        """بازخوانی داده‌ها."""
        pass