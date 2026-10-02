"""Setting Card: کارت گروهی برای تنظیمات."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

from src.ui.theme import Colors


class SettingCard(QFrame):
    """کارت گروهی برای تنظیمات."""

    def __init__(
        self,
        title: str,
        icon: str = "⚙️",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self.setObjectName("SettingCard")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # === Header ===
        header = QHBoxLayout()
        header.setSpacing(8)

        icon_label = QLabel(self._icon)
        icon_label.setStyleSheet("font-size: 16pt; background: transparent;")
        header.addWidget(icon_label)

        title_label = QLabel(self._title)
        title_label.setObjectName("CardTitle")
        title_label.setAlignment(Qt.AlignRight)
        header.addWidget(title_label, stretch=1)

        layout.addLayout(header)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {Colors.BORDER_LIGHT}; max-height: 1px;"
        )
        layout.addWidget(sep)

        # === Content ===
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)

    def add_row(self, label: str, value: str) -> None:
        """اضافه کردن یک ردیف label-value."""
        row = QHBoxLayout()
        row.setSpacing(10)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; background: transparent;"
        )
        label_widget.setAlignment(Qt.AlignRight)
        row.addWidget(label_widget)

        row.addStretch()

        value_widget = QLabel(value)
        value_widget.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-weight: bold; "
            "background: transparent;"
        )
        value_widget.setAlignment(Qt.AlignLeft)
        row.addWidget(value_widget)

        self.content_layout.addLayout(row)

    def add_widget(self, widget: QWidget) -> None:
        """اضافه کردن یک widget دلخواه."""
        self.content_layout.addWidget(widget)