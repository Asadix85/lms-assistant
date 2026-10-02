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
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # === ساعت ===
        if self._assignment.deadline:
            time_str = self._assignment.deadline.strftime("%H:%M")
            deadline_label = QLabel(f"{time_str}  ⏹️")
            deadline_label.setObjectName("CalEventDeadline")
            deadline_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(deadline_label)

        # === عنوان (کامل) ===
        title = QLabel(self._assignment.title)
        title.setObjectName("CalEventTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight | Qt.AlignTop)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        title.setToolTip(self._assignment.title)
        layout.addWidget(title)

    def _get_color(self) -> tuple[str, str, str]:
        """رنگ (پس‌زمینه‌ی شفاف، متن، حاشیه) بر اساس وضعیت ددلاین."""
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        if not self._assignment.deadline:
            color = c.TEXT_MUTED
        else:
            now = datetime.now()
            delta = self._assignment.deadline - now

            if delta.total_seconds() < 0:
                color = c.TEXT_MUTED
            elif delta.days == 0:
                color = c.ERROR
            elif delta.days == 1:
                color = c.ACCENT
            elif delta.days <= 3:
                color = c.WARNING
            else:
                color = c.SUCCESS

        # ⚠️ در dark، پس‌زمینه تیره‌تر با کمی رنگ
        if is_dark:
            # alpha بالاتر برای شفافیت مناسب
            bg = f"{color}30"  # 19% alpha
            bg_hover = f"{color}55"
            text_color = c.TEXT_PRIMARY  # ← روشن
            border_color = color
        else:
            bg = f"{color}22"
            bg_hover = f"{color}44"
            text_color = c.TEXT_PRIMARY
            border_color = color

        return bg, bg_hover, text_color, border_color

    def _apply_style(self) -> None:
        c = CurrentTheme.colors()
        bg, bg_hover, text_color, border_color = self._get_color()

        self.setStyleSheet(f"""
            QFrame#CalendarEventItem {{
                background-color: {bg};
                border-right: 3px solid {border_color};
                border-radius: 4px;
            }}
            QFrame#CalendarEventItem:hover {{
                background-color: {bg_hover};
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