"""Header: نوار بالای برنامه."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal, Qt


class Header(QFrame):
    """Header بالا."""

    update_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Header")
        self.setFixedHeight(70)

        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # === Left: User Info ===
        user_layout = QVBoxLayout()
        user_layout.setSpacing(2)

        self.user_name = QLabel("کاربر")
        self.user_name.setObjectName("HeaderTitle")
        user_layout.addWidget(self.user_name)

        self.user_status = QLabel("آماده")
        self.user_status.setObjectName("HeaderSubtitle")
        user_layout.addWidget(self.user_status)

        layout.addLayout(user_layout)
        layout.addStretch()

        # === Right: Update Button ===
        self.update_btn = QPushButton("🔄  بروزرسانی از LMS")
        self.update_btn.setObjectName("PrimaryButton")
        self.update_btn.setMinimumWidth(200)
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self.update_clicked.emit)
        layout.addWidget(self.update_btn)

    def set_user(self, name: str, status: str = "آماده") -> None:
        self.user_name.setText(name)
        self.user_status.setText(status)

    def set_busy(self, busy: bool, status: str = "") -> None:
        self.update_btn.setEnabled(not busy)
        if status:
            self.user_status.setText(status)