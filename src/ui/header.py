"""Header: نوار بالای برنامه با Circular Progress Button."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal, Qt

from src.services.sync_progress import SyncProgress
from src.ui.widgets.pill_progress import PillProgressButton

class Header(QFrame):
    """Header بالا با دکمه‌ی گرد progress."""

    update_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Header")
        self.setFixedHeight(110)

        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(20)

        # === ۱. اطلاعات کاربر (راست) ===
        user_layout = QVBoxLayout()
        user_layout.setSpacing(4)
        user_layout.setContentsMargins(0, 0, 0, 0)

        self.user_name = QLabel("خوش آمدید")
        self.user_name.setObjectName("HeaderTitle")
        self.user_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_layout.addWidget(self.user_name)

        self.user_status = QLabel("آماده")
        self.user_status.setObjectName("HeaderSubtitle")
        self.user_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_layout.addWidget(self.user_status)

        # === تغییرات زنده ===
        self.changes_label = QLabel("")
        self.changes_label.setObjectName("HeaderChanges")
        self.changes_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.changes_label.setVisible(False)
        user_layout.addWidget(self.changes_label)

        # === زمان ===
        self.elapsed_label = QLabel("")
        self.elapsed_label.setObjectName("HeaderElapsed")
        self.elapsed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.elapsed_label.setVisible(False)
        user_layout.addWidget(self.elapsed_label)

        layout.addLayout(user_layout, stretch=1)

        # === ۲. دکمه‌ی گرد (چپ) ===
        self.circular_btn = PillProgressButton()
        self.circular_btn.button.clicked.connect(self.update_clicked.emit)
        layout.addWidget(self.circular_btn, alignment=Qt.AlignVCenter)

    # === Public API ===

    def set_user(self, name: str | None, status: str = "آماده") -> None:
        """تنظیم نام کاربر و وضعیت."""
        if name:
            self.user_name.setText(f"{name} عزیز، خوش آمدید")
        else:
            self.user_name.setText("خوش آمدید")
        self.user_status.setText(status)

    def set_busy(self, busy: bool, status: str = "") -> None:
        """فعال/غیرفعال کردن حالت busy."""
        self.circular_btn.button.setEnabled(not busy)
        self.circular_btn.set_busy(busy)

        if status:
            self.user_status.setText(status)

        if not busy:
            self.changes_label.setVisible(False)
            self.elapsed_label.setVisible(False)

    def set_progress(self, progress: SyncProgress) -> None:
        """تنظیم progress کامل."""
        # درصد روی حلقه
        self.circular_btn.set_progress(progress.percent)

        # متن وضعیت
        if progress.message:
            self.user_status.setText(progress.message)

        # تغییرات زنده
        changes_text = progress.changes_text
        if changes_text:
            self.changes_label.setText(changes_text)
            self.changes_label.setVisible(True)
        else:
            self.changes_label.setVisible(False)

        # زمان
        if progress.elapsed > 0:
            self.elapsed_label.setText(
                f"⏱️ {progress.elapsed_text}"
            )
            self.elapsed_label.setVisible(True)