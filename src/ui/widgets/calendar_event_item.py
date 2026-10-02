"""Calendar Event Item: آیتم کوچک یک ددلاین در سلول تقویم."""

from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from src.models.assignment import Assignment
from src.ui.theme import CurrentTheme


class CalendarEventItem(QFrame):
    """آیتم کوچک یک ددلاین."""

    clicked = Signal(str)

    def __init__(self, assignment: Assignment, parent=None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("CalendarEventItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._build()
        self._apply_style()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(2)

        # === ساعت ===
        if self._assignment.deadline:
            time_str = self._assignment.deadline.strftime("%H:%M")
            deadline_label = QLabel(f"{time_str}  ⏹️")
            deadline_label.setObjectName("CalEventDeadline")
            deadline_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(deadline_label)

        # === عنوان ===
        title = QLabel(self._assignment.title)
        title.setObjectName("CalEventTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight | Qt.AlignTop)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        title.setToolTip(self._assignment.title)
        layout.addWidget(title)

    def _get_color(self) -> tuple[str, str, str, str]:
        """رنگ‌ها: (پس‌زمینه، پس‌زمینه hover، متن، بردر)"""
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        # رنگ بردر بر اساس وضعیت ددلاین
        if not self._assignment.deadline:
            color_hex = c.TEXT_MUTED.lstrip("#")
        else:
            now = datetime.now()
            delta = self._assignment.deadline - now

            if delta.total_seconds() < 0:
                color_hex = c.TEXT_MUTED.lstrip("#")
            elif delta.days == 0:
                color_hex = c.ERROR.lstrip("#")
            elif delta.days == 1:
                color_hex = c.ACCENT.lstrip("#")
            elif delta.days <= 3:
                color_hex = c.WARNING.lstrip("#")
            else:
                color_hex = c.SUCCESS.lstrip("#")

        # ⚠️ در dark، پس‌زمینه تیره‌تر با alpha بالاتر
        if is_dark:
            bg = f"rgba({int(color_hex[0:2], 16)}, {int(color_hex[2:4], 16)}, {int(color_hex[4:6], 16)}, 0.12)"
            bg_hover = f"rgba({int(color_hex[0:2], 16)}, {int(color_hex[2:4], 16)}, {int(color_hex[4:6], 16)}, 0.20)"
        else:
            bg = f"rgba({int(color_hex[0:2], 16)}, {int(color_hex[2:4], 16)}, {int(color_hex[4:6], 16)}, 0.08)"
            bg_hover = f"rgba({int(color_hex[0:2], 16)}, {int(color_hex[2:4], 16)}, {int(color_hex[4:6], 16)}, 0.15)"

        text_color = c.TEXT_PRIMARY
        border_color = f"#{color_hex}"

        return bg, bg_hover, text_color, border_color

    def _apply_style(self) -> None:
        bg, bg_hover, text_color, border_color = self._get_color()

        # ⚠️ border-right (در RTL به سمت راست بصری می‌ره)
        self.setStyleSheet(f"""
            QFrame#CalendarEventItem {{
                background-color: {bg};
                border-right: 4px solid {border_color};
                border-radius: 4px;
            }}
            QFrame#CalendarEventItem:hover {{
                background-color: {bg_hover};
                border-right: 6px solid {border_color};
            }}
            QLabel#CalEventTitle {{
                color: {text_color};
                font-size: 8pt;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#CalEventDeadline {{
                color: {border_color};
                font-size: 7pt;
                font-weight: bold;
                background: transparent;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._assignment.id)
        super().mousePressEvent(event)