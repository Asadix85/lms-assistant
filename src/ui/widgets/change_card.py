"""Change Card: کارت نمایش یک تغییر — نسخه‌ی بازطراحی‌شده."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.models.change import Change, ChangeType, EntityType
from src.ui.theme import CurrentTheme


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class ChangeCard(QFrame):
    """کارت نمایش یک تغییر با آیکون رنگی و پیل نوع."""

    TYPE_META = {
        ChangeType.NEW: ("🆕", "جدید", "#34C759"),
        ChangeType.UPDATED: ("🔄", "به‌روز", "#2AA6A3"),
        ChangeType.REMOVED: ("🗑️", "حذف", "#FF3B30"),
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
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(14)

        # --- آیکون ---
        type_icon, _type_text, type_color = self.TYPE_META.get(
            self._change.type, ("❓", "نامشخص", _c("TEXT_MUTED", "#8E8E93"))
        )

        icon_box = QFrame()
        icon_box.setFixedSize(52, 52)
        icon_box.setStyleSheet(
            f"background-color: {type_color}22; border-radius: 14px;"
        )
        icon_lay = QVBoxLayout(icon_box)
        icon_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(type_icon)
        icon_lbl.setStyleSheet("font-size: 18pt; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lay.addWidget(icon_lbl)
        lay.addWidget(icon_box)

        # --- محتوا ---
        content = QVBoxLayout()
        content.setSpacing(4)

        title = QLabel(self._get_title())
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-size: 11pt; "
            "font-weight: 700; background: transparent;"
        )
        content.addWidget(title)

        entity_icon, entity_text = self.ENTITY_META.get(
            self._change.entity_type, ("❓", "نامشخص")
        )
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        entity_pill = QLabel(f"{entity_icon} {entity_text}")
        entity_pill.setFixedHeight(22)
        entity_pill.setStyleSheet(
            f"color: {_c('TEXT_SECONDARY', '#3A3A3C')}; "
            f"background-color: {_c('BORDER_LIGHT', 'rgba(0,0,0,0.05)')}; "
            "border-radius: 11px; padding: 0 10px; font-size: 8pt; font-weight: 600;"
        )
        info_row.addWidget(entity_pill)

        type_pill = QLabel(_type_text)
        type_pill.setFixedHeight(22)
        type_pill.setStyleSheet(
            f"color: {type_color}; background-color: {type_color}22; "
            "border-radius: 11px; padding: 0 10px; font-size: 8pt; font-weight: 700;"
        )
        info_row.addWidget(type_pill)
        info_row.addStretch()
        content.addLayout(info_row)

        time_lbl = QLabel(self._change.detected_at.strftime("%Y-%m-%d %H:%M"))
        time_lbl.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8pt; background: transparent;"
        )
        content.addWidget(time_lbl)

        lay.addLayout(content, stretch=1)

    def _get_title(self) -> str:
        data = self._change.data or {}
        return data.get("name") or data.get("title") or self._change.entity_id

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        # بازسازی کامل کارت
        self._build()