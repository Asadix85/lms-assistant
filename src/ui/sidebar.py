"""Sidebar: منوی کنار با آیکون‌های SVG."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
)
from PySide6.QtCore import Signal, Qt, QSize

from src.ui.icons import Icons
from src.ui.theme import CurrentTheme


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
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 20, 8, 20)
        layout.setSpacing(4)

        # === Logo ===
        logo = QLabel("🎓  LMS Assistant")
        logo.setStyleSheet(
            f"font-size: 15pt; font-weight: bold; "
            f"color: {c.PRIMARY}; padding: 8px 0; background: transparent;"
        )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        subtitle = QLabel("دانشگاه اصفهان")
        subtitle.setStyleSheet(
            f"font-size: 9pt; color: {c.TEXT_MUTED}; padding: 0 0 8px 0; "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background-color: {c.BORDER_LIGHT}; margin: 8px 10px;"
        )
        layout.addWidget(sep)

        # === Menu Items ===
        menu_items = [
            ("dashboard", Icons.DASHBOARD, "داشبورد"),
            ("calendar", Icons.CALENDAR, "تقویم"),
            ("courses", Icons.COURSES, "دروس"),
            ("assignments", Icons.ASSIGNMENTS, "تکالیف"),
            ("events", Icons.EVENTS, "جلسات آنلاین"),
            ("changes", Icons.CHANGES, "تغییرات"),
            ("settings", Icons.SETTINGS, "تنظیمات"),
        ]

        for key, icon_name, label in menu_items:
            btn = self._make_button(icon_name, label)
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
            f"background-color: {c.BORDER_LIGHT}; margin: 8px 10px;"
        )
        layout.addWidget(sep2)

        # === About ===
        self.about_btn = self._make_button(Icons.ABOUT, "درباره من")
        self.about_btn.clicked.connect(lambda checked: self._on_click("about"))
        self._buttons["about"] = self.about_btn
        self._group.addButton(self.about_btn)
        layout.addWidget(self.about_btn)

        # === Version ===
        version = QLabel("نسخه 0.1.0")
        version.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 8pt; padding: 8px; "
            "background: transparent;"
        )
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

    def _make_button(self, icon_name: str, label: str) -> QPushButton:
        """ساخت یک دکمه‌ی Sidebar با آیکون SVG."""
        btn = QPushButton(f"  {label}")
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)

        # آیکون SVG
        icon = Icons.get(icon_name, size=22)
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))

        return btn

    def _on_click(self, key: str) -> None:
        self.page_changed.emit(key)

    def set_active(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)

    def refresh_icons(self) -> None:
        """رفرش آیکون‌ها (بعد از تغییر تم)."""
        Icons.clear_cache()

        icon_map = {
            "dashboard": Icons.DASHBOARD,
            "calendar": Icons.CALENDAR,
            "courses": Icons.COURSES,
            "assignments": Icons.ASSIGNMENTS,
            "events": Icons.EVENTS,
            "changes": Icons.CHANGES,
            "settings": Icons.SETTINGS,
            "about": Icons.ABOUT,
        }

        for key, btn in self._buttons.items():
            icon_name = icon_map.get(key)
            if icon_name:
                icon = Icons.get(icon_name, size=22)
                if not icon.isNull():
                    btn.setIcon(icon)