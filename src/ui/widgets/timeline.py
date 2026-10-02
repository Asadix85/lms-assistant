"""Horizontal Timeline: تایم‌لاین افقی (با هویت LMS Assistant)."""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from src.ui.theme import CurrentTheme


class TimelineItem(QFrame):
    """یک آیتم در تایم‌لاین افقی."""

    clicked = Signal(str)

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        is_active: bool = False,
        item_id: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle
        self._is_active = is_active
        self._item_id = item_id
        self.setObjectName("TimelineItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumWidth(140)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # === Dot (دایره) ===
        dot_container = QFrame()
        dot_container.setFixedHeight(30)
        dot_layout = QVBoxLayout(dot_container)
        dot_layout.setAlignment(Qt.AlignCenter)
        dot_layout.setContentsMargins(0, 0, 0, 0)

        self.dot = QLabel()
        self.dot.setObjectName("TimelineDot")
        self.dot.setFixedSize(16, 16)
        self.dot.setAlignment(Qt.AlignCenter)
        dot_layout.addWidget(self.dot)

        layout.addWidget(dot_container)

        # === Title ===
        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("TimelineTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # === Subtitle ===
        if self._subtitle:
            self.subtitle_label = QLabel(self._subtitle)
            self.subtitle_label.setObjectName("TimelineSubtitle")
            self.subtitle_label.setAlignment(Qt.AlignCenter)
            self.subtitle_label.setWordWrap(True)
            layout.addWidget(self.subtitle_label)

        self._apply_style()

    def _apply_style(self) -> None:
        c = CurrentTheme.colors()
        is_dark = CurrentTheme.is_dark()

        if self._is_active:
            dot_bg = c.PRIMARY
            title_color = c.PRIMARY
            dot_border = c.PRIMARY
            dot_size = 16
        else:
            dot_bg = "transparent"
            title_color = c.TEXT_SECONDARY
            dot_border = c.TEXT_MUTED if not is_dark else "#475569"
            dot_size = 14

        self.dot.setFixedSize(dot_size, dot_size)

        self.setStyleSheet(f"""
            QFrame#TimelineItem {{
                background: transparent;
                border: none;
            }}
            QLabel#TimelineDot {{
                background-color: {dot_bg};
                border: 2px solid {dot_border};
                border-radius: {dot_size // 2}px;
            }}
            QLabel#TimelineTitle {{
                color: {title_color};
                font-weight: bold;
                font-size: 10pt;
                background: transparent;
            }}
            QLabel#TimelineSubtitle {{
                color: {c.TEXT_SECONDARY};
                font-size: 9pt;
                background: transparent;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if self._item_id:
            self.clicked.emit(self._item_id)
        super().mousePressEvent(event)


class HorizontalTimeline(QWidget):
    """تایم‌لاین افقی (مثل یونیکو اما با هویت ما)."""

    item_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._build()

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Line + Items Container ===
        self.container = QFrame()
        self.container.setObjectName("TimelineContainer")
        self.container.setFixedHeight(130)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # === Line Background ===
        self.line = QFrame()
        self.line.setFixedHeight(2)
        self.line.setObjectName("TimelineLine")
        container_layout.addWidget(self.line)

        # === Items Row ===
        self.items_layout = QHBoxLayout()
        self.items_layout.setSpacing(0)
        self.items_layout.setContentsMargins(20, -8, 20, 8)
        container_layout.addLayout(self.items_layout)

        layout.addWidget(self.container)

    def set_items(self, items: list[dict]) -> None:
        """تنظیم آیتم‌ها.

        items: [
            {"id": "1", "title": "...", "subtitle": "...", "active": True},
            ...
        ]
        """
        # پاک کردن
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in items:
            widget = TimelineItem(
                title=item.get("title", ""),
                subtitle=item.get("subtitle", ""),
                is_active=item.get("active", False),
                item_id=item.get("id", ""),
            )
            widget.clicked.connect(self.item_clicked.emit)
            self.items_layout.addWidget(widget, stretch=1)