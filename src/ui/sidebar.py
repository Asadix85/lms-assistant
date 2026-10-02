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
        self.setFixedWidth(230)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 20, 8, 20)
        layout.setSpacing(4)

        # === Logo ===
        logo = QLabel("🎓  LMS Assistant")
        logo.setStyleSheet(
            "font-size: 15pt; font-weight: bold; padding: 8px 0; "
            "background: transparent;"
        )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        subtitle = QLabel("دانشگاه اصفهان")
        subtitle.setStyleSheet(
            "font-size: 9pt; opacity: 0.7; padding: 0 0 8px 0; "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.2); margin: 8px 10px;"
        )
        layout.addWidget(sep)

        # === Menu Items ===
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

        # === Separator ===
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(
            "background-color: rgba(148, 163, 184, 0.2); margin: 8px 10px;"
        )
        layout.addWidget(sep2)

        # === About Button ===
        self.about_btn = QPushButton("👤  درباره من")
        self.about_btn.setObjectName("SidebarButton")
        self.about_btn.setCheckable(True)
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.clicked.connect(lambda checked: self._on_click("about"))
        self._buttons["about"] = self.about_btn
        self._group.addButton(self.about_btn)
        layout.addWidget(self.about_btn)

        # === Version ===
        version = QLabel("نسخه 0.1.0")
        version.setStyleSheet(
            "opacity: 0.5; font-size: 8pt; padding: 8px; "
            "background: transparent;"
        )
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

    def _on_click(self, key: str) -> None:
        self.page_changed.emit(key)

    def set_active(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)