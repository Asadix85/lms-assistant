"""Effects: Shadow و Animation — هم‌تراز با Liquid Glass فیروزه‌ای."""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PySide6.QtGui import QColor


def add_shadow(
    widget: QWidget,
    blur_radius: int = 28,
    offset_x: int = 0,
    offset_y: int = 6,
    color: str | None = None,
) -> QGraphicsDropShadowEffect:
    """اضافه کردن سایه نرم به widget (مناسب کارت‌های glass).

    Args:
        widget: widget مورد نظر
        blur_radius: شعاع blur (بزرگ‌تر = نرم‌تر)
        offset_x: جابجایی افقی
        offset_y: جابجایی عمودی
        color: رنگ ARGB (#AARRGGBB). اگر None باشد از تم فعلی خوانده می‌شود.
    """
    if color is None:
        try:
            from src.ui.theme import CurrentTheme
            color = getattr(CurrentTheme.colors(), "SHADOW", "#1E507814")
        except Exception:
            color = "#1E507814"

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(offset_x)
    shadow.setYOffset(offset_y)
    shadow.setColor(QColor(color))
    widget.setGraphicsEffect(shadow)
    return shadow


def add_card_shadow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """سایه استاندارد کارت‌های glass."""
    return add_shadow(widget, blur_radius=26, offset_x=0, offset_y=6)


def add_soft_shadow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """سایه خیلی نرم برای المان‌های فرعی."""
    try:
        from src.ui.theme import CurrentTheme
        color = getattr(CurrentTheme.colors(), "SHADOW_SOFT", "#1E50780C")
    except Exception:
        color = "#1E50780C"
    return add_shadow(widget, blur_radius=18, offset_x=0, offset_y=3, color=color)


def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
    """انیمیشن Fade-in (روی windowOpacity — فقط برای پنجره)."""
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    return anim
