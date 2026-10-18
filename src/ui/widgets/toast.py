"""Toast: اعلان‌های شناور (Snackbar) پایین پنجره — جایگزین نرم QMessageBox.

استفاده:
    from src.ui.widgets.toast import show_toast

    show_toast(parent_window, "✅ همگام‌سازی انجام شد", kind="success")
"""

from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QRect,
    QEasingCurve,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QWidget,
)

from src.ui.icons import Icons
from src.ui.rtl import RTLWidgetMixin
from src.ui.theme import CurrentTheme

# نوع‌ها → (آیکون، رنگ پس‌زمینه روشن، رنگ پس‌زمینه تیره)
_KIND_META = {
    "success": (Icons.CHECK, "#2AA6A3", "#2AA6A3"),
    "info": (Icons.INFO, "#3B8EA5", "#4A7D97"),
    "warning": (Icons.WARNING, "#E08600", "#CC7F08"),
    "error": (Icons.ERROR, "#D9433A", "#C0392F"),
}

# نگه‌داشتن مرجع توست‌های فعال تا بسته شدن (جلوگیری از GC زودهنگام)
_active_toasts: set = set()


class Toast(RTLWidgetMixin, QWidget):
    """یک نوار اعلان شناور با انیمیشن slide-up + fade."""

    def __init__(
        self,
        window: QWidget,
        text: str,
        kind: str = "info",
        duration_ms: int = 3500,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._kind = kind if kind in _KIND_META else "info"
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build(text)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setYOffset(6)
        shadow.setColor(QColor("#00000066"))
        self.setGraphicsEffect(shadow)

        self.adjustSize()
        self._animations: list[QPropertyAnimation] = []
        self.show()
        self._slide_in()

        from PySide6.QtCore import QTimer

        QTimer.singleShot(duration_ms, self._slide_out)

    # ------------------------------------------------------------
    def _build(self, text: str) -> None:
        c = CurrentTheme.colors()
        icon_name, light_bg, dark_bg = _KIND_META[self._kind]
        bg = dark_bg if CurrentTheme.is_dark() else light_bg

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        pill = QWidget(self)
        pill.setObjectName("ToastPill")
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(16, 12, 10, 12)
        pill_layout.setSpacing(10)

        icon_lbl = QLabel(pill)
        icon_lbl.setPixmap(
            Icons.get(icon_name, size=18, color="#FFFFFF").pixmap(18, 18)
        )
        pill_layout.addWidget(icon_lbl)

        text_lbl = QLabel(text, pill)
        text_lbl.setWordWrap(True)
        text_lbl.setMaximumWidth(420)
        text_lbl.setStyleSheet(
            "color: #FFFFFF; background: transparent; font-weight: 500;"
        )
        pill_layout.addWidget(text_lbl)

        close_btn = QToolButton(pill)
        close_btn.setText("×")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QToolButton { color: rgba(255,255,255,0.85); border: none;"
            " background: transparent; font-size: 16pt; padding: 0 4px; }"
            "QToolButton:hover { color: white; }"
        )
        close_btn.clicked.connect(self._slide_out)
        pill_layout.addWidget(close_btn)

        pill.setStyleSheet(f"""
            QWidget#ToastPill {{
                background-color: {bg};
                border-radius: 14px;
            }}
        """)

        lay.addWidget(pill)
        self._pill = pill

    # ------------------------------------------------------------
    # Positioning & animation
    # ------------------------------------------------------------
    def _target_rect(self) -> QRect:
        area = self._window.rect()
        w = min(self.sizeHint().width(), area.width() - 40)
        h = self.sizeHint().height()
        x = area.center().x() - w // 2
        y = area.bottom() - h - 24
        return QRect(x, y, w, h)

    def _slide_in(self) -> None:
        target = self._target_rect()
        start = target.translated(0, 24)
        self.setGeometry(start)
        self.setWindowOpacity(0.0)

        geom = QPropertyAnimation(self, b"geometry", self)
        geom.setDuration(280)
        geom.setStartValue(start)
        geom.setEndValue(target)
        geom.setEasingCurve(QEasingCurve.OutCubic)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(220)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        self._animations = [geom, fade]
        for a in self._animations:
            a.start()

    def _slide_out(self) -> None:
        if getattr(self, "_closing", False):
            return
        self._closing = True
        current = QRect(self.geometry())
        target = current.translated(0, 18)

        geom = QPropertyAnimation(self, b"geometry", self)
        geom.setDuration(220)
        geom.setStartValue(current)
        geom.setEndValue(target)
        geom.setEasingCurve(QEasingCurve.InCubic)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(220)
        fade.setStartValue(self.windowOpacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InCubic)
        fade.finished.connect(self._finish)

        self._animations = [geom, fade]
        for a in self._animations:
            a.start()

    def _finish(self) -> None:
        _active_toasts.discard(self)
        self.deleteLater()

    def reposition(self) -> None:
        """با تغییر اندازه پنجره، توست جابه‌جا شود."""
        if not getattr(self, "_closing", False):
            self.setGeometry(self._target_rect())


def show_toast(
    window: QWidget,
    text: str,
    kind: str = "info",
    duration_ms: int = 3500,
) -> Toast | None:
    """نمایش یک Toast پایین وسط پنجره. اگر `window` معتبر نباشد، None."""
    if window is None:
        return None
    toast = Toast(window, text, kind=kind, duration_ms=duration_ms)
    _active_toasts.add(toast)
    return toast
