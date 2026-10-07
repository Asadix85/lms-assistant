"""CheckBox سفارشی با تیک SVG + RTL درست."""

from PySide6.QtCore import Qt, QSize, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QCheckBox,
    QWidget,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
)

from src.ui.theme import CurrentTheme


class CustomCheckBox(QWidget):
    """چک‌باکس سفارشی — چک‌باکس راست، متن بعدش.

    از QWidget + QHBoxLayout استفاده می‌کنه تا RTL درست کار کنه.
    """

    toggled = Signal(bool)

    BOX_SIZE = 22
    BORDER_RADIUS = 6
    BORDER_WIDTH = 2

    def __init__(
        self,
        text: str = "",
        parent=None,
        checked: bool = False,
    ) -> None:
        super().__init__(parent)
        self._text = text
        self._checked = checked
        self._enabled = True
        self._hovered = False

        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._build()

    def _build(self) -> None:
        # === layout افقی (در RTL: اول = راست) ===
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        # ۱. چک‌باکس indicator (راست‌ترین widget در RTL)
        self._box_widget = _CheckBoxIndicator(
            size=self.BOX_SIZE,
            radius=self.BORDER_RADIUS,
            border_width=self.BORDER_WIDTH,
            parent=self,
        )
        self._box_widget.setFixedSize(self.BOX_SIZE, self.BOX_SIZE)
        layout.addWidget(self._box_widget)

        # ۲. متن (بعد از چک‌باکس)
        self._text_label = QLabel(self._text, self)
        self._text_label.setStyleSheet("background: transparent;")
        self._text_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._text_label, stretch=1)

    # === Public API ===

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        self._text = text
        self._text_label.setText(text)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self._box_widget.set_checked(checked)
        self.update()
        self.toggled.emit(checked)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._enabled = enabled
        self._box_widget.set_enabled(enabled)
        self._update_text_color()

    def _update_text_color(self) -> None:
        c = CurrentTheme.colors()
        color = c.TEXT_PRIMARY if self._enabled else c.TEXT_MUTED
        self._text_label.setStyleSheet(
            f"color: {color}; background: transparent; "
            "font-size: 11pt;"
        )

    # === Events ===

    def mousePressEvent(self, event) -> None:
        if self._enabled and event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._box_widget.set_hovered(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._box_widget.set_hovered(False)
        self.update()
        super().leaveEvent(event)


class _CheckBoxIndicator(QWidget):
    """indicator سفارشی که با QPainter کشیده می‌شه."""

    def __init__(
        self,
        size: int = 22,
        radius: int = 6,
        border_width: int = 2,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._radius = radius
        self._border_width = border_width
        self._checked = False
        self._enabled = True
        self._hovered = False

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.update()

    def set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered
        self.update()

    def paintEvent(self, event) -> None:
        c = CurrentTheme.colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRect(0, 0, self._size, self._size)

        # === رنگ‌ها ===
        if not self._enabled:
            if self._checked:
                bg = QColor(c.TEXT_MUTED)
                border = QColor(c.TEXT_MUTED)
            else:
                bg = QColor(c.BORDER_LIGHT)
                border = QColor(c.BORDER)
        elif self._checked:
            bg = QColor(c.PRIMARY)
            border = QColor(c.PRIMARY)
        elif self._hovered:
            bg = QColor(c.GLASS_BG_HOVER)
            border = QColor(c.PRIMARY)
        else:
            bg = QColor(c.GLASS_BG)
            border = QColor(c.TEXT_MUTED)

        # === پس‌زمینه ===
        painter.setPen(QPen(border, self._border_width))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, self._radius, self._radius)

        # === تیک ===
        if self._checked:
            self._draw_check(painter, rect)

        painter.end()

    def _draw_check(self, painter: QPainter, rect: QRect) -> None:
        """نقاشی تیک سفید."""
        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()

        pen = QPen(QColor("white"), 3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        p1 = (x + w * 0.22, y + h * 0.5)
        p2 = (x + w * 0.42, y + h * 0.72)
        p3 = (x + w * 0.78, y + h * 0.28)

        painter.drawLine(*p1, *p2)
        painter.drawLine(*p2, *p3)