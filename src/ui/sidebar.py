"""Sidebar: منوی کنار با دو تیکه‌ی گرد (سبک مدرن)."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize

from src.ui.icons import Icons
from src.ui.theme import CurrentTheme


class Sidebar(QFrame):
    """منوی کنار راست با دو تیکه‌ی گرد."""

    page_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(240)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._build()

    def _build(self) -> None:
        # === Outer layout ===
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 14, 10, 14)
        outer.setSpacing(12)

        # === Separator ===
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setObjectName("SidebarSeparator")
        # ============================================
        # تیکه‌ی اول: کارت اصلی
        # ============================================
        top_card = QFrame()
        top_card.setObjectName("SidebarTopCard")
        top_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(8, 14, 8, 14)
        top_layout.setSpacing(4)

        # === Logo ===
        logo = QLabel("🎓  LMS Assistant")
        logo.setObjectName("SidebarLogo")
        logo.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(logo)

        # === Subtitle ===
        subtitle = QLabel("دانشگاه اصفهان")
        subtitle.setObjectName("SidebarSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(subtitle)

        # === Separator ===
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setObjectName("SidebarSeparator")
        top_layout.addWidget(sep1)

        top_layout.addSpacing(6)

        # === Menu Items ===
        menu_items = [
            ("dashboard", Icons.DASHBOARD, "داشبورد"),
            ("calendar", Icons.CALENDAR, "تقویم"),
            ("courses", Icons.COURSES, "دروس"),
            ("assignments", Icons.ASSIGNMENTS, "تکالیف"),
            ("events", Icons.EVENTS, "جلسات آنلاین"),
            ("changes", Icons.CHANGES, "تغییرات"),
        ]

        for key, icon_name, label in menu_items:
            btn = self._make_button(icon_name, label)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            self._buttons[key] = btn
            self._group.addButton(btn)
            top_layout.addWidget(btn)

        # === Stretch (پایین کارت اول) ===
        top_layout.addStretch()

        outer.addWidget(top_card, stretch=1)

        # ============================================
        # تیکه‌ی دوم: کارت پایین
        # ============================================
        bottom_card = QFrame()
        bottom_card.setObjectName("SidebarBottomCard")
        bottom_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        bottom_layout = QVBoxLayout(bottom_card)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(4)

        # === Settings Button ===
        settings_btn = self._make_button(Icons.SETTINGS, "تنظیمات")
        settings_btn.clicked.connect(lambda checked: self._on_click("settings"))
        self._buttons["settings"] = settings_btn
        self._group.addButton(settings_btn)
        bottom_layout.addWidget(settings_btn)

        # === Separator ===
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setObjectName("SidebarSeparator")
        bottom_layout.addWidget(sep2)

        # === About Button ===
        about_btn = self._make_button(Icons.ABOUT, "درباره من")
        about_btn.clicked.connect(lambda checked: self._on_click("about"))
        self._buttons["about"] = about_btn
        self._group.addButton(about_btn)
        bottom_layout.addWidget(about_btn)

        # === Version ===
        version = QLabel("نسخه 0.1.0")
        version.setObjectName("SidebarVersion")
        version.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(version)

        outer.addWidget(bottom_card)

        # === Set Active Default ===
        self._buttons["dashboard"].setChecked(True)

    def _make_button(self, icon_name: str, label: str) -> QPushButton:
        btn = QPushButton(f"{label}")
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(42)
        btn.setLayoutDirection(Qt.LeftToRight)  # ⚠️ برای مرکز

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
                    btn.setIconSize(QSize(22, 22))