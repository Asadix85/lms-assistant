"""Contents Page: فایل‌ها و محتواهای تمام دروس."""

from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.content import Content
from src.storage.database import Database
from src.storage.repositories import ContentRepository, CourseRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.empty_state import EmptyState


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


_TYPE_META = {
    "pdf": ("📄", "#FF3B30"),
    "zip": ("📦", "#FF9500"),
    "rar": ("📦", "#FF9500"),
    "docx": ("📝", "#2B579A"),
    "doc": ("📝", "#2B579A"),
    "pptx": ("📊", "#D24726"),
    "ppt": ("📊", "#D24726"),
    "xlsx": ("📗", "#217346"),
    "xls": ("📗", "#217346"),
    "mp4": ("🎬", "#3B8EA5"),
    "jpg": ("🖼️", "#34C759"),
    "jpeg": ("🖼️", "#34C759"),
    "png": ("🖼️", "#34C759"),
}


class ContentRow(QFrame):
    """ردیف یک فایل محتوا."""

    def __init__(self, content: Content, course_name: str = "", parent=None) -> None:
        super().__init__(parent)
        self._content = content
        self.setObjectName("ContentRow")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(64)

        icon, color = _TYPE_META.get(
            (content.content_type or "").lower(),
            ("📎", _c("PRIMARY", "#2AA6A3")),
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(14)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background-color: {color}18; border-radius: 12px; font-size: 16pt;"
        )
        lay.addWidget(icon_lbl)

        col = QVBoxLayout()
        col.setSpacing(3)
        title = QLabel(content.title or content.filename or "فایل")
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 700; "
            f"font-size: 10.5pt; background: transparent;"
        )
        col.addWidget(title)

        meta_parts = []
        if course_name:
            meta_parts.append(course_name)
        if content.content_type:
            meta_parts.append(content.content_type.upper())
        meta = QLabel(" · ".join(meta_parts) if meta_parts else "—")
        meta.setStyleSheet(
            f"color: {_c('TEXT_MUTED', '#8E8E93')}; font-size: 8.5pt; background: transparent;"
        )
        col.addWidget(meta)
        lay.addLayout(col, stretch=1)

        open_btn = QPushButton("باز کردن")
        open_btn.setObjectName("SoftButton")
        open_btn.setFixedHeight(34)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self._open)
        lay.addWidget(open_btn)

        self.setStyleSheet(f"""
            QFrame#ContentRow {{
                background-color: {_c('GLASS_BG', 'rgba(255,255,255,0.55)')};
                border: 1px solid {_c('GLASS_BORDER', 'rgba(0,0,0,0.08)')};
                border-radius: 16px;
            }}
            QFrame#ContentRow:hover {{
                background-color: {_c('GLASS_BG_HOVER', 'rgba(255,255,255,0.88)')};
                border-color: {_c('GLASS_BORDER_HOVER', 'rgba(42,166,163,0.4)')};
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._open()
        super().mousePressEvent(event)

    def _open(self) -> None:
        if self._content.url:
            QDesktopServices.openUrl(QUrl(self._content.url))


class ContentsPage(BasePage):
    """صفحه‌ی محتواها و فایل‌های دروس."""

    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._contents: list[Content] = []
        self._course_map: dict[str, str] = {}
        self._filter_type = "all"
        super().__init__(
            title="محتواها",
            subtitle="فایل‌ها و منابع تمام دروس",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        toolbar = QFrame()
        toolbar.setObjectName("Card")
        toolbar.setFixedHeight(60)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(15, 10, 15, 10)
        tb.setSpacing(8)

        self._filter_btns: dict[str, QPushButton] = {}
        for key, label in (
            ("all", "همه"),
            ("pdf", "PDF"),
            ("zip", "آرشیو"),
            ("other", "سایر"),
        ):
            btn = QPushButton(label)
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(70)
            btn.clicked.connect(lambda checked=False, k=key: self._set_filter(k))
            if key == "all":
                btn.setChecked(True)
            self._filter_btns[key] = btn
            tb.addWidget(btn)

        tb.addStretch()
        self.content_layout.addWidget(toolbar)

        self.counter = QLabel("")
        self.counter.setObjectName("PageSubtitle")
        self.counter.setAlignment(Qt.AlignRight)
        self.counter.setContentsMargins(0, 8, 12, 0)
        self.content_layout.addWidget(self.counter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(8, 8, 8, 20)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def _set_filter(self, key: str) -> None:
        self._filter_type = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        self._render()

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._contents = ContentRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_map = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter.setText(f"خطا: {e}")
            return
        self._render()

    def _matches(self, c: Content) -> bool:
        t = (c.content_type or "").lower()
        if self._filter_type == "all":
            return True
        if self._filter_type == "pdf":
            return t == "pdf"
        if self._filter_type == "zip":
            return t in ("zip", "rar", "7z")
        return t not in ("pdf", "zip", "rar", "7z")

    def _render(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = [c for c in self._contents if self._matches(c)]
        self.counter.setText(f"{len(items)} فایل")

        if not items:
            empty = EmptyState(
                icon_name="file",
                title="محتوایی نیست",
                description="بعد از همگام‌سازی، فایل‌های دروس اینجا نمایش داده می‌شوند.",
                action_text="همگام‌سازی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)
            self.list_layout.addWidget(empty)
            return

        # گروه‌بندی بر اساس درس
        by_course: dict[str, list[Content]] = defaultdict(list)
        for c in items:
            by_course[c.course_id].append(c)

        for course_id, group in by_course.items():
            name = self._course_map.get(course_id, "درس نامشخص")
            head = QLabel(f"📚  {name}  ·  {len(group)} فایل")
            head.setObjectName("SectionTitle")
            head.setStyleSheet(
                f"color: {_c('TEXT_PRIMARY', '#1C1C1E')}; font-weight: 800; "
                f"font-size: 11pt; padding: 10px 4px 6px 4px; background: transparent;"
            )
            self.list_layout.addWidget(head)
            for c in group:
                self.list_layout.addWidget(ContentRow(c, name))

        self.list_layout.addStretch()

    def refresh_theme(self) -> None:
        super().refresh_theme()
        self._render()
