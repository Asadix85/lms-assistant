"""Posts Page: پیام‌های وال تمام دروس."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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

from src.models.post import Post
from src.storage.database import Database
from src.storage.repositories import CourseRepository, PostRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import CurrentTheme
from src.ui.widgets.empty_state import EmptyState
from src.ui.widgets.post_card import PostCard


def _c(name: str, fallback: str) -> str:
    return str(getattr(CurrentTheme.colors(), name, fallback))


class PostsPage(BasePage):
    """صفحه‌ی پیام‌های وال LMS."""

    sync_requested = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._posts: list[Post] = []
        self._course_map: dict[str, str] = {}
        self._filter = "all"
        super().__init__(
            title="پیام‌های وال",
            subtitle="آخرین پیام‌های اساتید و همکلاسی‌ها",
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
        tb.setSpacing(10)

        self.btn_all = self._filter_btn("همه", "all")
        self.btn_new = self._filter_btn("🆕 جدید", "new")
        tb.addWidget(self.btn_all)
        tb.addWidget(self.btn_new)
        tb.addStretch()

        self.btn_mark = QPushButton("✓ علامت‌گذاری همه به‌عنوان دیده‌شده")
        self.btn_mark.setObjectName("SecondaryButton")
        self.btn_mark.setFixedHeight(36)
        self.btn_mark.clicked.connect(self._mark_seen)
        tb.addWidget(self.btn_mark)

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
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(8, 8, 8, 20)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def _filter_btn(self, text: str, key: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("FilterButton")
        btn.setCheckable(True)
        btn.setFixedHeight(36)
        btn.setMinimumWidth(80)
        btn.clicked.connect(lambda: self._set_filter(key))
        if key == "all":
            btn.setChecked(True)
        return btn

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self.btn_all.setChecked(key == "all")
        self.btn_new.setChecked(key == "new")
        self._render()

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                self._posts = PostRepository(db).get_all()
                courses = CourseRepository(db).get_all()
                self._course_map = {c.id: c.name for c in courses}
        except Exception as e:
            self.counter.setText(f"خطا: {e}")
            return
        self._render()

    def _render(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        posts = self._posts
        if self._filter == "new":
            posts = [p for p in posts if getattr(p, "is_new", False)]

        new_count = sum(1 for p in self._posts if getattr(p, "is_new", False))
        self.counter.setText(
            f"{len(posts)} پیام"
            + (f" · {new_count} جدید" if new_count else "")
        )

        if not posts:
            empty = EmptyState(
                icon_name="inbox",
                title="پیامی نیست",
                description="بعد از همگام‌سازی، پیام‌های وال اینجا دیده می‌شوند.",
                action_text="همگام‌سازی",
            )
            empty.action_clicked.connect(self.sync_requested.emit)
            self.list_layout.addWidget(empty)
            return

        for post in posts:
            course = self._course_map.get(post.course_id, "")
            wrap = QFrame()
            wrap.setObjectName("Card")
            wlay = QVBoxLayout(wrap)
            wlay.setContentsMargins(0, 0, 0, 0)
            wlay.setSpacing(0)

            if course:
                chip = QLabel(f"📚  {course}")
                chip.setStyleSheet(
                    f"color: {_c('PRIMARY', '#2AA6A3')}; font-size: 9pt; font-weight: 700; "
                    f"background: {_c('PRIMARY_LIGHT', 'rgba(42,166,163,0.12)')}; "
                    "padding: 8px 16px; border-top-left-radius: 16px; border-top-right-radius: 16px;"
                )
                wlay.addWidget(chip)

            card = PostCard(post)
            # جلوگیری از double-radius روی کارت داخلی
            card.setStyleSheet(card.styleSheet() + "QFrame#PostCard { border: none; border-radius: 0; }")
            wlay.addWidget(card)
            self.list_layout.addWidget(wrap)

        self.list_layout.addStretch()

    def _mark_seen(self) -> None:
        try:
            with Database(self.db_path) as db:
                PostRepository(db).mark_all_seen()
        except Exception:
            pass
        self.refresh()

    def refresh_theme(self) -> None:
        super().refresh_theme()
        self._render()
