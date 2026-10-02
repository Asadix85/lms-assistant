"""Icons: مدیریت آیکون‌های SVG."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

from src.ui.theme import CurrentTheme


class Icons:
    """مدیریت آیکون‌ها."""

    ICONS_DIR = Path("assets/icons")

    # نام آیکون‌ها
    DASHBOARD = "chart-pie"
    CALENDAR = "calendar-days"
    COURSES = "book"
    ASSIGNMENTS = "clipboard-list"
    EVENTS = "video"
    CHANGES = "bell"
    SETTINGS = "gear"
    ABOUT = "user"
    UPDATE = "rotate"
    THEME_LIGHT = "sun"
    THEME_DARK = "moon"
    DOWNLOAD = "download"
    EXTERNAL = "arrow-up-right-from-square"
    CHECK = "circle-check"
    WARNING = "triangle-exclamation"
    ERROR = "circle-xmark"
    INFO = "circle-info"
    CLOCK = "clock"
    USER = "user"
    GRADUATION = "graduation-cap"
    FIRE = "fire"
    STAR = "star"

    _cache: dict = {}

    @classmethod
    def get(cls, name: str, size: int = 24, color: str | None = None) -> QIcon:
        """دریافت آیکون به عنوان QIcon.

        Args:
            name: نام آیکون (بدون .svg)
            size: اندازه به پیکسل
            color: رنگ (اگر None، از تم فعلی استفاده می‌شه)
        """
        key = f"{name}_{size}_{color}"
        if key in cls._cache:
            return cls._cache[key]

        # مسیر فایل
        icon_path = cls.ICONS_DIR / f"{name}.svg"
        if not icon_path.exists():
            print(f"⚠️ آیکون پیدا نشد: {icon_path}")
            return QIcon()

        # رنگ پیش‌فرض
        if color is None:
            color = CurrentTheme.colors().TEXT_PRIMARY

        # رندر SVG
        pixmap = cls._render_svg(icon_path, size, color)
        icon = QIcon(pixmap)

        cls._cache[key] = icon
        return icon

    @classmethod
    def _render_svg(cls, path: Path, size: int, color: str) -> QPixmap:
        """رندر SVG با رنگ دلخواه."""
        renderer = QSvgRenderer(str(path))

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)

        # اعمال رنگ
        if color:
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()

        return pixmap

    @classmethod
    def clear_cache(cls) -> None:
        """پاک کردن cache (برای تغییر تم)."""
        cls._cache.clear()