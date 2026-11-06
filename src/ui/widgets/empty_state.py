"""Empty State: پیام زیبا برای صفحات خالی — هم‌سطح liquid glass دسکتاپ."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.ui.icons import Icons
from src.ui.theme import CurrentTheme, Radius
from src.ui.rtl import RTLWidgetMixin


class EmptyState(RTLWidgetMixin, QWidget):
    """Empty State زیبا با آیکون دایره‌ای + پیام + دکمه‌ی action."""

    action_clicked = Signal()

    def __init__(
        self,
        icon_name: str,
        title: str,
        description: str = "",
        action_text: str = "",
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self._title = title
        self._description = description
        self._action_text = action_text
        self._compact = compact
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        if self._compact:
            icon_size = 36
            circle = 56
            title_size = 12
            desc_size = 10
            padding_top = 20
            padding_bottom = 20
        else:
            icon_size = 48
            circle = 80
            title_size = 14
            desc_size = 11
            padding_top = 48
            padding_bottom = 48

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8 if self._compact else 12)
        layout.setContentsMargins(20, padding_top, 20, padding_bottom)

        # === Icon circle (glass accent) ===
        icon_wrap = QFrame()
        icon_wrap.setObjectName("EmptyIconCircle")
        icon_wrap.setFixedSize(circle, circle)
        icon_wrap.setStyleSheet(
            f"""
            QFrame#EmptyIconCircle {{
                background-color: {c.PRIMARY_LIGHT};
                border: 1px solid {getattr(c, 'PRIMARY_RING', c.PRIMARY_LIGHT)};
                border-radius: {circle // 2}px;
            }}
            """
        )
        icon_lay = QVBoxLayout(icon_wrap)
        icon_lay.setContentsMargins(0, 0, 0, 0)
        icon_lay.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon = Icons.get(self._icon_name, size=icon_size, color=c.PRIMARY)
        if not icon.isNull():
            icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
        else:
            icon_label.setText("📭")
            icon_label.setStyleSheet(
                f"font-size: {icon_size // 2}pt; background: transparent; color: {c.PRIMARY};"
            )
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        icon_lay.addWidget(icon_label)
        layout.addWidget(icon_wrap, alignment=Qt.AlignCenter)

        # === Title ===
        title = QLabel(self._title)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: 800; "
            f"font-size: {title_size}pt; "
            f"background: transparent; padding: {4 if self._compact else 8}px 0;"
        )
        layout.addWidget(title)

        # === Description ===
        if self._description:
            desc = QLabel(self._description)
            desc.setAlignment(Qt.AlignCenter)
            desc.setWordWrap(True)
            desc.setMaximumWidth(420)
            desc.setStyleSheet(
                f"color: {c.TEXT_SECONDARY}; font-size: {desc_size}pt; "
                "background: transparent;"
            )
            layout.addWidget(desc)

        # === Action button ===
        if self._action_text:
            btn = QPushButton(self._action_text)
            btn.setObjectName("PrimaryButton")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumWidth(160 if self._compact else 200)
            btn.setMinimumHeight(40)
            btn.clicked.connect(self.action_clicked.emit)
            layout.addSpacing(6 if self._compact else 10)
            layout.addWidget(btn, alignment=Qt.AlignCenter)
