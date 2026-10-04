"""Header: نوار بالای برنامه با Loading Bar و Welcome."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)
from PySide6.QtCore import Signal, Qt


class Header(QFrame):
    """Header بالا با Loading Bar."""

    update_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Header")
        self.setFixedHeight(90)

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Main Row ===
        main_row = QWidget()
        main_layout = QHBoxLayout(main_row)
        main_layout.setContentsMargins(24, 12, 24, 12)
        main_layout.setSpacing(20)

        # ⚠️ در RTL سراسری:
        # - اولین widget = راست‌ترین
        # - آخرین widget = چپ‌ترین

        # === ۱. اطلاعات کاربر (اول = راست‌ترین) ===
        user_layout = QVBoxLayout()
        user_layout.setSpacing(2)
        user_layout.setContentsMargins(0, 0, 0, 0)

        self.user_name = QLabel("خوش آمدید")
        self.user_name.setObjectName("HeaderTitle")
        self.user_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_layout.addWidget(self.user_name)

        self.user_status = QLabel("آماده")
        self.user_status.setObjectName("HeaderSubtitle")
        self.user_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        user_layout.addWidget(self.user_status)

        main_layout.addLayout(user_layout)

        # === ۲. فاصله (stretch) ===
        main_layout.addStretch(1)

        # === ۳. دکمه‌ی Update + Progress (آخر = چپ‌ترین) ===
        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.progress = QProgressBar()
        self.progress.setObjectName("HeaderProgress")
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)

        self.update_btn = QPushButton("📡  بروزرسانی از LMS")
        self.update_btn.setObjectName("PrimaryButton")
        self.update_btn.setMinimumWidth(220)
        self.update_btn.setMinimumHeight(44)
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self.update_clicked.emit)

        right_layout.addWidget(self.progress)
        right_layout.addWidget(self.update_btn)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

        layout.addWidget(main_row)

    def set_user(self, name: str | None, status: str = "آماده") -> None:
        """تنظیم نام کاربر و وضعیت."""
        if name:
            self.user_name.setText(f"{name} عزیز، خوش آمدید")
        else:
            self.user_name.setText("خوش آمدید")
        self.user_status.setText(status)

    def set_busy(self, busy: bool, status: str = "") -> None:
        """فعال/غیرفعال کردن حالت busy."""
        self.update_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

        if busy:
            self.update_btn.setText("⏳  در حال بروزرسانی...")
        else:
            self.update_btn.setText("📡  بروزرسانی از LMS")

        if status:
            self.user_status.setText(status)

    def set_progress(self, value: int) -> None:
        """تنظیم مقدار پیشرفت (0-100)."""
        if value < 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(value)