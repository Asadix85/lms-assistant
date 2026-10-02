"""Sidebar: منوی کنار."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
)
from PySide6.QtCore import Signal, Qt


class Sidebar(QFrame):
    """منوی کنار راست."""

    page_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)
        # ⚠️ هیچ setLayoutDirection اینجا نذار (QApplication سراسری)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)

        # Logo
        logo = QLabel("🎓  LMS Assistant")
        logo.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #00C4C4; "
            "padding: 15px 10px;"
        )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        subtitle = QLabel("دانشگاه اصفهان")
        subtitle.setStyleSheet(
            "font-size: 9pt; color: #7F8C8D; padding: 0 10px 15px 10px;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #E1E4E8; max-height: 1px; margin: 10px;")
        layout.addWidget(sep)

        # Menu Items
        menu_items = [
            ("dashboard", "📊", "داشبورد"),
            ("calendar", "📅", "تقویم"),
            ("courses", "📚", "دروس"),
            ("assignments", "📋", "تکالیف"),
            ("events", "🎥", "جلسات آنلاین"),
            ("changes", "🔔", "تغییرات"),
            ("settings", "⚙️", "تنظیمات"),
        ]

        for key, icon, label in menu_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))

            self._buttons[key] = btn
            self._group.addButton(btn)
            layout.addWidget(btn)

        self._buttons["dashboard"].setChecked(True)

        layout.addStretch()

        version = QLabel("نسخه 0.1.0")
        version.setStyleSheet("color: #BDC3C7; font-size: 8pt; padding: 10px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

    def _on_click(self, key: str) -> None:
        self.page_changed.emit(key)

    def set_active(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)