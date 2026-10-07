"""Setting Card: کارت گروهی برای تنظیمات."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen

from src.ui.theme import CurrentTheme


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
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # === Header ===
        header = QHBoxLayout()
        header.setSpacing(12)

        # Icon در یه دایره‌ی رنگی
        icon_container = QFrame()
        icon_container.setFixedSize(38, 38)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {c.PRIMARY_LIGHT};
                border-radius: 19px;
                border: none;
            }}
        """)

        icon_label = QLabel(self._icon, icon_container)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setGeometry(0, 0, 38, 38)
        icon_label.setStyleSheet(
            "font-size: 16pt; background: transparent; border: none;"
        )

        header.addWidget(icon_container)

        title_label = QLabel(self._title)
        title_label.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
            "font-size: 13pt; background: transparent; border: none;"
        )
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(title_label, stretch=1)

        layout.addLayout(header)

        # === Separator ===
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background-color: {c.BORDER_LIGHT}; max-height: 1px;"
        )
        layout.addWidget(sep)

        # === Content ===
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        layout.addLayout(self.content_layout)

    def add_row(self, label: str, value: str) -> None:
        """اضافه کردن یک ردیف label-value."""
        c = CurrentTheme.colors()

        row = QHBoxLayout()
        row.setSpacing(10)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; background: transparent; "
            "font-size: 10pt;"
        )
        label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(label_widget)

        row.addStretch()

        value_widget = QLabel(value)
        value_widget.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; "
            "font-size: 11pt; background: transparent;"
        )
        value_widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(value_widget)

        self.content_layout.addLayout(row)

    def add_widget(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)