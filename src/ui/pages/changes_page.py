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
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from src.models.change import Change, ChangeType
from src.storage.database import Database
from src.storage.repositories import ChangeRepository
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors
from src.ui.widgets.change_card import ChangeCard


class ChangesPage(BasePage):
    sync_requested = Signal()
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

        # === Toolbar Modern ===
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("Card") # استفاده از استایل کارت برای تولبار
        toolbar_frame.setFixedHeight(60)

        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(15, 10, 15, 10)
        toolbar.setSpacing(10)

        # دکمه‌های فیلتر با استایل Pill
        self.btn_all = self._create_filter_btn("همه", "all")
        self.btn_new = self._create_filter_btn("🆕 جدید", "new")
        self.btn_removed = self._create_filter_btn("🗑️ حذف شده", "removed")

        toolbar.addWidget(self.btn_all)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_removed)

        toolbar.addStretch()

        self.btn_clear = QPushButton("🗑️ پاک کردن تاریخچه")
        self.btn_clear.setObjectName("SecondaryButton")
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.clicked.connect(self._clear_all)
        toolbar.addWidget(self.btn_clear)

        self.content_layout.addWidget(toolbar_frame)

        # === Counter ===
        self.counter_label = QLabel("")
        self.counter_label.setObjectName("PageSubtitle")
        self.counter_label.setAlignment(Qt.AlignRight)
        self.counter_label.setContentsMargins(0, 10, 20, 0)
        self.content_layout.addWidget(self.counter_label)

        # === Scroll ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_widget.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Minimum,
        )

        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(20, 10, 20, 20)
        self.list_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.list_widget)
        self.content_layout.addWidget(scroll, stretch=1)

    def _create_filter_btn(self, text: str, filter_key: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("FilterButton")
        btn.setCheckable(True)
        btn.setFixedHeight(36)
        btn.setMinimumWidth(80)
        btn.clicked.connect(lambda: self._set_filter(filter_key))
        if filter_key == "all":
            btn.setChecked(True)
        return btn

    def refresh(self) -> None:
        try:
            with Database(self.db_path) as db:
                repo = ChangeRepository(db)
                self._all_changes = repo.get_all(limit=200)
        except Exception as e:
            self.counter_label.setText(f"خطا در دریافت داده: {e}")
            return
        self._apply_filters()

    def _apply_filters(self) -> None:
        changes = list(self._all_changes)

        if self._filter == "new":
            changes = [c for c in changes if c.type == ChangeType.NEW]
        elif self._filter == "removed":
            changes = [c for c in changes if c.type == ChangeType.REMOVED]

        self.counter_label.setText(
            f"نمایش {len(changes)} مورد از {len(self._all_changes)} تغییر"
        )

        # پاک کردن لیست قبلی
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not changes:
            self._show_empty_state()
            return

        for c in changes:
            card = ChangeCard(c)
            self.list_layout.addWidget(card)

        self.list_widget.adjustSize()

    def _show_empty_state(self) -> None:
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🍃")
        icon.setStyleSheet("font-size: 48pt; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel("هیچ تغییری ثبت نشده")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: " + Colors.TEXT_PRIMARY + "; background: transparent;")
        title.setAlignment(Qt.AlignCenter)

        desc = QLabel("از آخرین همگام‌سازی، تغییر جدیدی در سیستم دیده نشده است.")
        desc.setStyleSheet("font-size: 10pt; color: " + Colors.TEXT_SECONDARY + "; background: transparent;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)

        btn_sync = QPushButton("🔄 همگام‌سازی دستی")
        btn_sync.setObjectName("PrimaryButton")
        btn_sync.setFixedWidth(150)
        btn_sync.clicked.connect(self.sync_requested.emit)

        empty_layout.addWidget(icon)
        empty_layout.addWidget(title)
        empty_layout.addWidget(desc)
        empty_layout.addSpacing(20)
        empty_layout.addWidget(btn_sync)

        self.list_layout.addWidget(empty_widget)

    def _set_filter(self, f: str) -> None:
        self._filter = f
        self.btn_all.setChecked(f == "all")
        self.btn_new.setChecked(f == "new")
        self.btn_removed.setChecked(f == "removed")
        self._apply_filters()

    def _clear_all(self) -> None:
        reply = QMessageBox.question(
            self,
            "پاک کردن تاریخچه",
            "آیا مطمئنی می‌خوای همه‌ی سوابق تغییرات رو پاک کنی؟\nاین عمل غیرقابل بازگشت است.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with Database(self.db_path) as db:
                ChangeRepository(db).delete_all()
            self.refresh()

    def refresh_theme(self) -> None:
        """بعد از تغییر تم."""
        self._apply_filters()