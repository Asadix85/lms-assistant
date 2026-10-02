"""Change Card: کارت نمایش یک تغییر."""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Qt

from src.models.change import Change, ChangeType, EntityType
from src.ui.theme import Colors


class ChangeCard(QFrame):
    """کارت نمایش یک تغییر."""

    TYPE_META = {
        ChangeType.NEW: ("🆕", "جدید", Colors.SUCCESS),
        ChangeType.UPDATED: ("🔄", "به‌روز", Colors.INFO),
        ChangeType.REMOVED: ("🗑️", "حذف", Colors.ERROR),
    }

    ENTITY_META = {
        EntityType.COURSE: ("📚", "درس"),
        EntityType.CONTENT: ("📄", "فایل"),
        EntityType.EVENT: ("📅", "رویداد"),
    }

    def __init__(self, change: Change, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._change = change
        self.setObjectName("ChangeCard")
        self.setMinimumHeight(90)
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(15)

        # === Icon Box ===
        type_icon, type_text, type_color = self.TYPE_META.get(
            self._change.type, ("❓", "نامشخص", Colors.TEXT_MUTED)
        )

        icon_box = QFrame()
        icon_box.setObjectName("ChangeIconBox")
        icon_box.setFixedSize(60, 60)
        icon_box.setStyleSheet(
            f"QFrame#ChangeIconBox {{ "
            f"background-color: {type_color}22; "
            f"border-radius: 10px; }}"
        )

        icon_layout = QVBoxLayout(icon_box)
        icon_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(type_icon)
        icon_label.setStyleSheet("font-size: 20pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)

        layout.addWidget(icon_box)

        # === Content ===
        content = QVBoxLayout()
        content.setSpacing(3)

        # Title (from data)
        title = self._get_title()
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignRight)
        content.addWidget(title_label)

        # Entity type + Change type
        entity_icon, entity_text = self.ENTITY_META.get(
            self._change.entity_type, ("❓", "نامشخص")
        )
        info = QLabel(f"{entity_icon} {entity_text}  •  {type_text}")
        info.setStyleSheet(
            f"color: {type_color}; font-size: 9pt; background: transparent;"
        )
        info.setAlignment(Qt.AlignRight)
        content.addWidget(info)

        # Time
        time_str = self._change.detected_at.strftime("%Y-%m-%d %H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 8pt; background: transparent;"
        )
        time_label.setAlignment(Qt.AlignRight)
        content.addWidget(time_label)

        layout.addLayout(content, stretch=1)

    def _get_title(self) -> str:
        """گرفتن عنوان از data."""
        data = self._change.data or {}
        # عنوان از data
        if "name" in data:
            return data["name"]
        if "title" in data:
            return data["title"]
        return f"{self._change.entity_id}"