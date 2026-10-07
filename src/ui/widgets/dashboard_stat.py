"""Dashboard Stat: کارت آماری ساده برای داشبورد."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from src.ui.theme import CurrentTheme


class DashboardStat(QFrame):
    """کارت آماری کوچک (آیکون + عدد + برچسب)."""

    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        color: str = "primary",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        c = CurrentTheme.colors()

        # رنگ بر اساس نوع
        colors = {
            "primary": c.PRIMARY,
            "success": c.SUCCESS,
            "warning": c.WARNING,
            "error": c.ERROR,
            "info": c.INFO,
        }
        accent = colors.get(color, c.PRIMARY)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # === آیکون + عدد (یه ردیف) ===
        top_row = QFrame()
        top_row.setStyleSheet("background: transparent; border: none;")

        from PySide6.QtWidgets import QHBoxLayout
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        top_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            f"font-size: 20pt; background: transparent; border: none;"
        )
        top_layout.addWidget(icon_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color: {accent}; font-weight: bold; font-size: 24pt; "
            "background: transparent; border: none;"
        )
        top_layout.addWidget(self.value_label)

        layout.addWidget(top_row)

        # === برچسب ===
        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent; border: none;"
        )
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)