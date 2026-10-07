"""Dashboard Stat: کارت آماری ساده برای داشبورد."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import Qt


class DashboardStat(QFrame):
    """کارت آماری کوچک (آیکون + عدد + برچسب)."""

    # رنگ‌های accent (ثابت — فرقی بین تم‌ها نداره)
    ACCENT_COLORS = {
        "primary": "PRIMARY",
        "success": "SUCCESS",
        "warning": "WARNING",
        "error": "ERROR",
        "info": "INFO",
    }

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

        self._accent = color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # === آیکون + عدد (یه ردیف) ===
        top_row = QWidget()
        top_row.setStyleSheet("background: transparent; border: none;")
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)
        top_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(icon)
        icon_label.setObjectName("DashboardStatIcon")
        top_layout.addWidget(icon_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("DashboardStatValue")
        # ⚠️ رنگ accent رو با property ذخیره می‌کنیم
        self.value_label.setProperty("accent", self._accent)
        top_layout.addWidget(self.value_label)

        layout.addWidget(top_row)

        # === برچسب ===
        label_widget = QLabel(label)
        label_widget.setObjectName("DashboardStatLabel")
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)

        # اعمال رنگ accent
        self._apply_accent_color()

    def _apply_accent_color(self) -> None:
        """اعمال رنگ accent (inline — برای هر کارت)."""
        from src.ui.theme import CurrentTheme
        c = CurrentTheme.colors()

        # اگه accent primary یا success بود، رنگ‌ش رو از تم بگیر
        accent_map = {
            "primary": c.PRIMARY,
            "success": c.SUCCESS,
            "warning": c.WARNING,
            "error": c.ERROR,
            "info": c.INFO,
        }
        color = accent_map.get(self._accent, c.PRIMARY)

        # ⚠️ فقط رنگ رو ست می‌کنیم، بقیه از QSS میاد
        self.value_label.setStyleSheet(f"color: {color};")

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def refresh_style(self) -> None:
        """بعد از تغییر تم صدا زده بشه."""
        self._apply_accent_color()