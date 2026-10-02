"""Effects: Shadow و Animation."""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PySide6.QtGui import QColor


def add_shadow(
    widget: QWidget,
    blur_radius: int = 30,
    offset_x: int = 0,
    offset_y: int = 5,
    color: str = "#00000050",
) -> QGraphicsDropShadowEffect:
    """اضافه کردن سایه به یک widget.

    Args:
        widget: widget مورد نظر
        blur_radius: شعاع blur (بزرگ‌تر = نرم‌تر). پیش‌فرض ۳۰.
        offset_x: جابجایی افقی
        offset_y: جابجایی عمودی (پیش‌فرض ۵ برای عمق)
        color: رنگ ARGB (#AARRGGBB)
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(offset_x)
    shadow.setYOffset(offset_y)
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)
    return shadow


def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """انیمیشن Fade-in (روی windowOpacity — فقط برای پنجره)."""
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    return anim