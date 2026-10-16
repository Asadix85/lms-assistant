"""دکمه‌ی بیضی با حلقه‌ی progress دور آن (پادساعتگرد)."""

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPropertyAnimation,
    QEasingCurve,
    Property,
)
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from src.ui.rtl import RTLWidgetMixin


class PillProgressButton(RTLWidgetMixin, QWidget):
    """دکمه‌ی بیضی با حلقه‌ی progress دور آن.

    - حلقه‌ی بیرونی: درصد پیشرفت (0-100) پادساعتگرد
    - دکمه‌ی وسط: قابل کلیک
    """

    RING_MARGIN = 6
    RING_WIDTH = 3

    # متن‌ها
    TEXT_IDLE = "🔄  بروزرسانی"
    TEXT_BUSY = "⏳  در حال بروزرسانی..."

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(260, 58)

        # === دکمه‌ی وسط ===
        self.button = QPushButton(self.TEXT_IDLE, self)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.setFixedHeight(40)

        # inline styleSheet
        self._apply_button_style()

        # چیدمان
        layout = QHBoxLayout(self)
        m = self.RING_MARGIN + 3
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(0)
        layout.addWidget(self.button)

        # state
        self._value = 0
        self._busy = False

        # انیمیشن
        self._animation = QPropertyAnimation(self, b"value")
        self._animation.setDuration(400)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def _apply_button_style(self) -> None:
        from src.ui.theme import CurrentTheme
        c = CurrentTheme.colors()

        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.PRIMARY};
                color: {c.TEXT_WHITE};
                border: none;
                border-radius: 20px;
                font-size: 11pt;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {c.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {c.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {c.TEXT_MUTED};
            }}
        """)

    def get_value(self) -> int:
        return self._value

    def set_value(self, value: int) -> None:
        self._value = max(0, min(100, value))
        self.update()

    value = Property(int, get_value, set_value)

    def set_progress(self, value: int, animated: bool = True) -> None:
        if animated:
            self._animation.stop()
            self._animation.setStartValue(self._value)
            self._animation.setEndValue(value)
            self._animation.start()
        else:
            self.set_value(value)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        if busy:
            self.button.setText(self.TEXT_BUSY)
        else:
            self.button.setText(self.TEXT_IDLE)
            self.set_progress(0, animated=True)
        self.update()

    def refresh_style(self) -> None:
        self._apply_button_style()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        margin = self.RING_MARGIN
        rect = QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
        )
        radius = rect.height() / 2

        # path دور بیضی
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # حلقه‌ی پس‌زمینه
        pen_bg = QPen(QColor(180, 180, 180, 70), self.RING_WIDTH)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawPath(path)

        # حلقه‌ی progress
        if self._value > 0:
            from src.ui.theme import CurrentTheme
            c = CurrentTheme.colors()

            pen_fg = QPen(QColor(c.PRIMARY), self.RING_WIDTH)
            pen_fg.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fg)

            n = 400
            n_progress = int(n * self._value / 100)
            START_OFFSET = 0.25

            prev_pt = path.pointAtPercent(START_OFFSET)
            for i in range(1, n_progress + 1):
                t = (START_OFFSET - i / n) % 1.0
                pt = path.pointAtPercent(t)
                painter.drawLine(prev_pt, pt)
                prev_pt = pt

        painter.end()