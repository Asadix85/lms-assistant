"""More Page: سایر امکانات — خلوت‌کردن سایدبار مثل نسخه‌ی وب."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme, Radius


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


# (key_or_url, emoji, title, desc, is_external)
_TILES: list[tuple[str, str, str, str, bool]] = [
    ("posts", "💬", "پیام‌های وال", "آخرین پیام‌های اساتید و همکلاسی‌ها", False),
    ("contents", "📄", "محتواها", "فایل‌ها و منابع تمام دروس", False),
    ("map", "📍", "نقشه مکان‌ها", "ساختمان‌های کلاس‌های شما", False),
    ("quera", "⚙️", "کوئرا", "تمرین‌ها و کلاس‌های کوئرا", False),
    ("analytics", "📊", "آمار", "نمای آماری از وضعیت دروس و تکالیف", False),
    ("changes", "🔔", "تغییرات", "تاریخچه موارد جدید و حذف‌شده", False),
    ("https://lms4.ui.ac.ir/pages/nodemain", "🏠", "پنل LMS", "ورود به صفحه اصلی سامانه LMS", True),
    ("https://lms4.ui.ac.ir/pages/messages", "📥", "صندوق پیام LMS", "پیام‌های خصوصی سامانه", True),
]


class MoreTile(QFrame):
    """کارت قابل کلیک برای یک قابلیت."""

    activated = Signal(str, bool)  # key_or_url, is_external

    def __init__(
        self,
        key: str,
        emoji: str,
        title: str,
        desc: str,
        is_external: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._key = key
        self._external = is_external
        self.setObjectName("MoreTile")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 16)
        lay.setSpacing(8)

        icon = QLabel(emoji)
        icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        icon.setStyleSheet(
            f"font-size: 28pt; background: transparent; padding: 0;"
        )
        lay.addWidget(icon)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignRight)
        title_lbl.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#FFFFFF')}; font-weight: 800; "
            f"font-size: 12pt; background: transparent;"
        )
        lay.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignRight)
        desc_lbl.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 9pt; background: transparent;"
        )
        lay.addWidget(desc_lbl)
        lay.addStretch()

        self._apply_style(False)

    def _apply_style(self, hover: bool) -> None:
        bg = _c("GLASS_BG_HOVER" if hover else "GLASS_BG", "rgba(28,38,38,0.68)")
        border = _c(
            "GLASS_BORDER_HOVER" if hover else "GLASS_BORDER",
            "rgba(255,255,255,0.12)",
        )
        self.setStyleSheet(f"""
            QFrame#MoreTile {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {Radius.LG}px;
            }}
        """)

    def enterEvent(self, event) -> None:
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.activated.emit(self._key, self._external)
        super().mousePressEvent(event)


class MorePage(BasePage):
    """سایر امکانات — جایگزین شلوغی سایدبار."""

    navigate = Signal(str)  # page key

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            title="سایر امکانات",
            subtitle="ابزارهای جانبی و میانبرهای سامانه",
            parent=parent,
        )

    def _build(self) -> None:
        super()._build()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(8, 8, 8, 24)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setAlignment(Qt.AlignTop)

        cols = 3
        for i, (key, emoji, title, desc, external) in enumerate(_TILES):
            tile = MoreTile(key, emoji, title, desc, external)
            tile.activated.connect(self._on_tile)
            grid.addWidget(tile, i // cols, i % cols)

        scroll.setWidget(host)
        self.content_layout.addWidget(scroll, stretch=1)

    def _on_tile(self, key: str, is_external: bool) -> None:
        if is_external:
            QDesktopServices.openUrl(QUrl(key))
            return
        self.navigate.emit(key)

    def refresh_theme(self) -> None:
        super().refresh_theme()
        # بازسازی استایل کاشی‌ها
        self._rebuild_tiles()

    def _rebuild_tiles(self) -> None:
        # ساده‌ترین راه: پاک و دوباره بساز
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # header از BasePage در layout اصلی است؛ فقط content را دوباره بساز
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(8, 8, 8, 24)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setAlignment(Qt.AlignTop)

        cols = 3
        for i, (key, emoji, title, desc, external) in enumerate(_TILES):
            tile = MoreTile(key, emoji, title, desc, external)
            tile.activated.connect(self._on_tile)
            grid.addWidget(tile, i // cols, i % cols)

        scroll.setWidget(host)
        self.content_layout.addWidget(scroll, stretch=1)
