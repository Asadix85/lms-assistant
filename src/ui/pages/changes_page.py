"""Changes Page: نمایش تغییرات اخیر."""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from src.models.change import Change, ChangeType
from src.storage.database import Database
from src.storage.repositories import ChangeRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.change_card import ChangeCard


class ChangesPage(BasePage):
    """صفحه‌ی تغییرات."""

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        self._all_changes: list[Change] = []
        self._filter: str = "all"
        super().__init__(
            title="تغییرات",
            subtitle="آخرین تغییرات در LMS شما",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Toolbar ===
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.btn_all = QPushButton("همه")
        self.btn_all.setObjectName("FilterButton")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self._set_filter("all"))
        toolbar.addWidget(self.btn_all)

        self.btn_new = QPushButton("🆕 جدید")
        self.btn_new.setObjectName("FilterButton")
        self.btn_new.setCheckable(True)
        self.btn_new.clicked.connect(lambda: self._set_filter("new"))
        toolbar.addWidget(self.btn_new)

        self.btn_removed = QPushButton("🗑️ حذف")
        self.btn_removed.setObjectName("FilterButton")
        self.btn_removed.setCheckable(True)
        self.btn_removed.clicked.connect(lambda: self._set_filter("removed"))
        toolbar.addWidget(self.btn_removed)

        toolbar.addStretch()

        self.btn_clear = QPushButton("🗑️ پاک کردن همه")
        self.btn_clear.setObjectName("FilterButton")
        self.btn_clear.clicked.connect(self._clear_all)
        toolbar.addWidget(self.btn_clear)

        self.content_layout.addLayout(toolbar)

        # === Counter ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.content_layout.addWidget(self.counter_label)

        # === Scroll ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Minimum,
        )

        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                repo = ChangeRepository(db)
                self._all_changes = repo.get_all(limit=200)
        except Exception as e:
            self.counter_label.setText(f"خطا: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        changes = list(self._all_changes)

        if self._filter == "new":
            changes = [c for c in changes if c.type == ChangeType.NEW]
        elif self._filter == "removed":
            changes = [c for c in changes if c.type == ChangeType.REMOVED]

        self.counter_label.setText(
            f"نمایش {len(changes)} از {len(self._all_changes)} تغییر"
        )

        # پاک کردن
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not changes:
            empty = QLabel("📭  هیچ تغییری ثبت نشده. یک بار Sync بزن.")
            empty.setObjectName("PageSubtitle")
            empty.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty)
            return

        for c in changes:
            card = ChangeCard(c)
            self.list_layout.addWidget(card)

        # تنظیم ارتفاع نهایی
        self.list_widget.adjustSize()

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_all.setChecked(f == "all")
        self.btn_new.setChecked(f == "new")
        self.btn_removed.setChecked(f == "removed")
        self._apply_filters()

    def _clear_all(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "پاک کردن تغییرات",
            "آیا مطمئنی می‌خوای همه‌ی تغییرات رو پاک کنی؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            with Database(self.db_path) as db:
                ChangeRepository(db).delete_all()
            self.refresh()