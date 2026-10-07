"""Sidebar: منوی کنار با آیکون قابل کلیک و collapse."""

from pathlib import Path

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QButtonGroup,
    QSizePolicy,
    QWidget,
)
from PySide6.QtCore import (
    Signal, Qt, QSize, QPropertyAnimation, QEasingCurve, QEvent,
)
from PySide6.QtGui import QPixmap, QCursor

from src.ui.icons import Icons
from src.ui.theme import CurrentTheme


class ClickableIcon(QLabel):
    """آیکون قابل کلیک (برای toggle سایدبار)."""

    clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        # افکت hover (اختیاری)
        self.setStyleSheet(
            "background: rgba(0,122,255,0.08); "
            "border-radius: 12px; border: none;"
        )
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.setStyleSheet("background: transparent; border: none;")
        super().leaveEvent(event)


class Sidebar(QFrame):
    """منوی کنار راست با آیکون قابل کلیک."""

    page_changed = Signal(str)

    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 72

    # سایز آیکون در دو حالت
    ICON_SIZE_EXPANDED = 80
    ICON_SIZE_COLLAPSED = 40

    APP_ICON_PATH = Path("assets/icons/app.png")

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self._is_collapsed = False
        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        # انیمیشن عرض
        self._animation = QPropertyAnimation(self, b"minimumWidth")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)

        self._build()
        self.setFixedWidth(self.EXPANDED_WIDTH)

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 14, 10, 14)
        outer.setSpacing(12)

        # ============================================
        # کارت اصلی
        # ============================================
        top_card = QFrame()
        top_card.setObjectName("SidebarTopCard")
        top_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(12, 24, 12, 16)  # ← padding بیشتر بالا
        top_layout.setSpacing(8)

        # === آیکون app (قابل کلیک برای toggle) ===
        self._app_icon = ClickableIcon()
        self._app_icon.clicked.connect(self.toggle_collapse)
        self._load_app_icon(size=self.ICON_SIZE_EXPANDED)

        # wrap در container برای وسط‌چین افقی
        icon_container = QWidget()
        icon_container.setStyleSheet("background: transparent;")
        icon_layout = QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self._app_icon)
        top_layout.addWidget(icon_container)

        # === اسم برنامه ===
        self._logo_text = QLabel("LMS Assistant")
        self._logo_text.setObjectName("SidebarLogo")
        self._logo_text.setAlignment(Qt.AlignCenter)
        top_layout.addWidget(self._logo_text)

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
            ("analytics", Icons.CHART_LINE, "آمار"),
            ("changes", Icons.CHANGES, "تغییرات"),
        ]

        for key, icon_name, label in menu_items:
            btn = self._make_button(icon_name, label)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            self._buttons[key] = btn
            self._group.addButton(btn)
            top_layout.addWidget(btn)

        top_layout.addStretch()
        outer.addWidget(top_card, stretch=1)

        # ============================================
        # کارت پایین
        # ============================================
        bottom_card = QFrame()
        bottom_card.setObjectName("SidebarBottomCard")
        bottom_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        bottom_layout = QVBoxLayout(bottom_card)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(4)

        settings_btn = self._make_button(Icons.SETTINGS, "تنظیمات")
        settings_btn.clicked.connect(lambda checked: self._on_click("settings"))
        self._buttons["settings"] = settings_btn
        self._group.addButton(settings_btn)
        bottom_layout.addWidget(settings_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setObjectName("SidebarSeparator")
        bottom_layout.addWidget(sep2)

        about_btn = self._make_button(Icons.ABOUT, "درباره من")
        about_btn.clicked.connect(lambda checked: self._on_click("about"))
        self._buttons["about"] = about_btn
        self._group.addButton(about_btn)
        bottom_layout.addWidget(about_btn)

        self._version = QLabel("نسخه 0.1.0")
        self._version.setObjectName("SidebarVersion")
        self._version.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self._version)

        outer.addWidget(bottom_card)

        self._buttons["dashboard"].setChecked(True)

    def _load_app_icon(self, size: int) -> None:
        """لود آیکون app."""
        if not self.APP_ICON_PATH.exists():
            self._app_icon.setText("🎓")
            self._app_icon.setStyleSheet(
                f"font-size: {size // 2}pt; "
                "background: transparent; border: none;"
            )
            return

        pixmap = QPixmap(str(self.APP_ICON_PATH))
        if pixmap.isNull():
            self._app_icon.setText("🎓")
            return

        pixmap = pixmap.scaled(
            size, size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._app_icon.setPixmap(pixmap)
        self._app_icon.setFixedSize(size, size)

    def _make_button(self, icon_name: str, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("SidebarButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(42)
        btn.setLayoutDirection(Qt.LeftToRight)

        icon = Icons.get(icon_name, size=22)
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))

        btn.setProperty("fullText", label)
        return btn

    def _on_click(self, key: str) -> None:
        self.page_changed.emit(key)

    def set_active(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)

    def refresh_icons(self) -> None:
        icon_map = {
            "dashboard": Icons.DASHBOARD,
            "calendar": Icons.CALENDAR,
            "courses": Icons.COURSES,
            "assignments": Icons.ASSIGNMENTS,
            "events": Icons.EVENTS,
            "analytics": Icons.CHART_LINE,
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

    # ============================================
    # Collapse / Expand
    # ============================================

    def toggle_collapse(self) -> None:
        self._is_collapsed = not self._is_collapsed

        target_width = (
            self.COLLAPSED_WIDTH if self._is_collapsed
            else self.EXPANDED_WIDTH
        )

        self._animation.stop()
        self._animation.setStartValue(self.width())
        self._animation.setEndValue(target_width)
        self._animation.start()

        self._update_content_visibility()

    def _update_content_visibility(self) -> None:
        """نمایش/مخفی کردن متن‌ها و تغییر سایز آیکون."""
        if self._is_collapsed:
            # آیکون کوچیک
            self._load_app_icon(size=self.ICON_SIZE_COLLAPSED)

            # مخفی کردن متن‌ها
            self._logo_text.setVisible(False)
            self._version.setVisible(False)

            # دکمه‌ها: فقط آیکون
            for btn in self._buttons.values():
                btn.setText("")
                btn.setToolTip(btn.property("fullText"))
        else:
            # آیکون بزرگ
            self._load_app_icon(size=self.ICON_SIZE_EXPANDED)

            # نمایش متن‌ها
            self._logo_text.setVisible(True)
            self._version.setVisible(True)

            # دکمه‌ها: با متن
            for btn in self._buttons.values():
                full_text = btn.property("fullText")
                btn.setText(full_text)
                btn.setToolTip("")