"""Assignment Card: کارت نمایش یک تکلیف."""

from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices

from src.models.assignment import Assignment
from src.ui.theme import Colors


class AssignmentCard(QFrame):
    """کارت نمایش یک تکلیف."""

    submit_clicked = Signal(str)

    def __init__(self, assignment: Assignment, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._assignment = assignment
        self.setObjectName("AssignmentCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)

        # === Title (کامل، بدون برش) ===
        title = QLabel(self._assignment.title)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignRight | Qt.AlignTop)
        # ⚠️ اجازه بده QLabel ارتفاع کامل بگیره
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title.setToolTip(self._assignment.title)
        layout.addWidget(title)

        # === Time Box ===
        time_box = QFrame()
        time_box.setObjectName("AssignmentTimeBox")

        time_layout = QVBoxLayout(time_box)
        time_layout.setContentsMargins(12, 10, 12, 10)
        time_layout.setSpacing(6)

        # Start
        start_text = self._assignment.start_at_jalali or self._format_dt(
            self._assignment.start_at
        )
        if start_text:
            time_layout.addWidget(
                self._build_time_row(
                    icon="▶️",
                    label="شروع تمرین:",
                    value=start_text,
                    color=Colors.SUCCESS,
                )
            )

        # Deadline
        end_text = self._assignment.deadline_jalali or self._format_dt(
            self._assignment.deadline
        )
        if end_text:
            time_layout.addWidget(
                self._build_time_row(
                    icon="⏹️",
                    label="پایان تمرین:",
                    value=end_text,
                    color=Colors.ERROR,
                )
            )

        # Status
        time_layout.addWidget(self._build_status_row())

        layout.addWidget(time_box)

        # === Actions ===
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()

        if self._assignment.submit_url:
            submit_btn = QPushButton("📤  ارسال پاسخ")
            submit_btn.setObjectName("PrimaryButton")
            submit_btn.setCursor(Qt.PointingHandCursor)
            submit_btn.clicked.connect(self._on_submit)
            actions.addWidget(submit_btn)

        if self._assignment.view_url:
            view_btn = QPushButton("👁️  نظر استاد")
            view_btn.setObjectName("SecondaryButton")
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.clicked.connect(self._on_view)
            actions.addWidget(view_btn)

        layout.addLayout(actions)

        # ⚠️ اجبار به تنظیم اندازه
        self.adjustSize()

    def _build_time_row(self, icon, label, value, color) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 10pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedWidth(24)
        row.addWidget(icon_label)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        label_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label_widget.setFixedWidth(90)
        row.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(
            f"color: {color}; font-size: 10pt; font-weight: bold; "
            "background: transparent;"
        )
        value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(value_widget, stretch=1)

        return container

    def _build_status_row(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        deadline_icon, deadline_color, deadline_text = self._get_deadline_info()

        icon_label = QLabel(deadline_icon)
        icon_label.setStyleSheet("font-size: 11pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedWidth(24)
        row.addWidget(icon_label)

        status_label = QLabel(deadline_text)
        status_label.setStyleSheet(
            f"color: {deadline_color}; font-weight: bold; font-size: 10pt; "
            "background: transparent;"
        )
        status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(status_label, stretch=1)

        if self._assignment.response_count > 0:
            count_label = QLabel(f"👥  {self._assignment.response_count} پاسخ")
            count_label.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; font-size: 9pt; "
                "background: transparent;"
            )
            count_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row.addWidget(count_label)

        return container

    def _get_deadline_info(self):
        if not self._assignment.deadline:
            return "⏰", Colors.TEXT_MUTED, "بدون ددلاین"

        now = datetime.now()
        delta = self._assignment.deadline - now

        if delta.total_seconds() < 0:
            return "⏹️", Colors.TEXT_MUTED, "مهلت گذشته"
        elif delta.days == 0:
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return "🔥", Colors.ERROR, f"امروز! {hours} ساعت و {minutes} دقیقه مانده"
        elif delta.days == 1:
            hours = delta.seconds // 3600
            return "⚠️", Colors.ACCENT, f"فردا! {hours} ساعت مانده"
        elif delta.days <= 3:
            return "⏰", Colors.WARNING, f"{delta.days} روز مانده"
        else:
            return "📅", Colors.SUCCESS, f"{delta.days} روز مانده"

    @staticmethod
    def _format_dt(dt) -> str:
        if not dt:
            return ""
        return dt.strftime("%Y-%m-%d %H:%M")

    def _on_submit(self) -> None:
        if self._assignment.submit_url:
            QDesktopServices.openUrl(QUrl(self._assignment.submit_url))
        self.submit_clicked.emit(self._assignment.id)

    def _on_view(self) -> None:
        if self._assignment.view_url:
            QDesktopServices.openUrl(QUrl(self._assignment.view_url))