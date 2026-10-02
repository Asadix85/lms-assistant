"""Windows Blur (Acrylic) — نسخه بهبودیافته.

از Windows DWM API برای blur واقعی استفاده می‌کنه.
"""

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtWidgets import QWidget


# === Constants ===

ACCENT_DISABLED = 0
ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
ACCENT_ENABLE_HOSTBACKDROP = 5


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENT_POLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]


WCA_ACCENT_POLICY = 19


def _is_windows() -> bool:
    return sys.platform == "win32"


def enable_blur(
    widget: QWidget,
    color: int = 0x99000000,
    enable: bool = True,
    accent_state: int = ACCENT_ENABLE_GRADIENT,  # ← از ACRYLIC به GRADIENT
    accent_flags: int = 2,                        # ← 2 برای blur + tint
) -> bool:
    """فعال‌سازی Acrylic Blur.

    Args:
        widget: widget مورد نظر
        color: رنگ tint (ARGB). نکته: alpha رو حتماً تنظیم کن.
            - برای لایت: `0xCCFFFFFF` (سفید ۸۰%)
            - برای دارک: `0xCC0F172A` (Slate تیره ۸۰%)
        enable: True برای فعال
        accent_state: نوع blur
        accent_flags: flags اضافی
    """
    if not _is_windows():
        return False

    try:
        hwnd = int(widget.winId())

        accent = ACCENT_POLICY()
        accent.AccentState = accent_state if enable else ACCENT_DISABLED
        accent.AccentFlags = accent_flags
        accent.GradientColor = color
        accent.AnimationId = 0

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)

        user32 = ctypes.windll.user32
        result = user32.SetWindowCompositionAttribute(
            wintypes.HWND(hwnd),
            ctypes.byref(data),
        )
        return bool(result)

    except Exception as e:
        print(f"⚠️ خطا در فعال‌سازی blur: {e}")
        return False


def disable_blur(widget: QWidget) -> bool:
    return enable_blur(widget, color=0, enable=False)


def enable_solid_color(widget: QWidget, color: int) -> bool:
    """رنگ ساده بدون blur (fallback)."""
    return enable_blur(
        widget,
        color=color,
        enable=True,
        accent_state=ACCENT_ENABLE_GRADIENT,
        accent_flags=0,
    )