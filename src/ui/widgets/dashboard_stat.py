"""Dashboard Stat: کارت آماری — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from src.ui.theme import CurrentTheme
from src.ui.rtl import RTLWidgetMixin


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class DashboardStat(RTLWidgetMixin, QFrame):
    """کارت آماری با آیکون گرادیانتی و افکت hover."""

    ACCENT_MAP = {
        "primary": ("PRIMARY", "PRIMARY_DARK"),
        "success": ("SUCCESS", "SUCCESS"),
        "warning": ("WARNING", "WARNING"),
        "error": ("ERROR", "ERROR"),
        "info": ("INFO", "INFO"),
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
        self.setFixedHeight(130)
        self._accent = color
        self._build(icon, value, label)

    def _build(self, icon: str, value: str, label: str) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignCenter)

        # --- ردیف بالا: آیکون + عدد ---
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.setAlignment(Qt.AlignCenter)

        # آیکون در باکس گرادیانتی
        primary_key, dark_key = self.ACCENT_MAP.get(self._accent, ("PRIMARY", "PRIMARY_DARK"))
        primary_color = _c(primary_key, "#2AA6A3")
        dark_color = _c(dark_key, "#1E807E")

        icon_box = QFrame()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {primary_color}, stop:1 {dark_color});
                border-radius: 14px;
            }}
        """)
        icon_lay = QVBoxLayout(icon_box)
        icon_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18pt; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lay.addWidget(icon_lbl)
        top_row.addWidget(icon_box)

        # عدد
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {primary_color};
            font-size: 22pt;
            font-weight: 800;
            background: transparent;
        """)
        top_row.addWidget(self.value_label)
        lay.addLayout(top_row)

        # --- برچسب ---
        label_lbl = QLabel(label)
        label_lbl.setAlignment(Qt.AlignCenter)
        label_lbl.setStyleSheet(f"""
            color: {_c('TEXT_SECONDARY', '#3A3A3C')};
            font-size: 9.5pt;
            font-weight: 600;
            background: transparent;
        """)
        lay.addWidget(label_lbl)

        # افکت hover بر اساس تم
        is_dark = CurrentTheme.is_dark()
        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        self.setStyleSheet(f"""
               QFrame#StatCard {{
                   background-color: {card_bg};
                   border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                   border-radius: 16px;
               }}
               QFrame#StatCard:hover {{
                   background-color: {card_hover};
                   border-color: {primary_color}60;
               }}
        """)

    def refresh_theme(self) -> None:
        """بعد از تغییر تم، استایل رو به‌روز کن."""
        primary_key, dark_key = self.ACCENT_MAP.get(self._accent, ("PRIMARY", "PRIMARY_DARK"))
        primary_color = _c(primary_key, "#2AA6A3")

        is_dark = CurrentTheme.is_dark()
        if is_dark:
            card_bg = "rgba(28, 38, 38, 0.75)"
            card_hover = "rgba(44, 54, 54, 0.85)"
        else:
            card_bg = "rgba(255, 255, 255, 0.85)"
            card_hover = "#FFFFFF"

        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: {card_bg};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
            QFrame#StatCard:hover {{
                background-color: {card_hover};
                border-color: {primary_color}60;
            }}
        """)

        # به‌روزرسانی رنگ عدد
        self.value_label.setStyleSheet(f"""
            color: {primary_color};
            font-size: 22pt;
            font-weight: 800;
            background: transparent;
        """)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def refresh_style(self) -> None:
        """بعد از تغییر تم."""
        # بازسازی کامل برای اعمال رنگ‌های جدید
        icon = self.findChild(QLabel)
        value = self.value_label.text()
        label = self.findChildren(QLabel)[-1].text() if len(self.findChildren(QLabel)) > 1 else ""
        self._build(icon.text() if icon else "📊", value, label)