"""Header: نوار بالای برنامه با Circular Progress Button."""

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal, Qt

from src.services.sync_progress import SyncProgress
from src.ui.widgets.pill_progress import PillProgressButton

class Header(QFrame):
    """Header بالا با دکمه‌ی گرد progress."""

    update_clicked = Signal()
    publish_clicked = Signal()

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

        # === ۲. دکمه‌ی انتشار GitHub (چپ، کنار دکمه گرد) ===
        self.publish_btn = QPushButton("🚀 انتشار")
        self.publish_btn.setObjectName("PublishButton")
        self.publish_btn.setCursor(Qt.PointingHandCursor)
        self.publish_btn.setToolTip(
            "ارسال دیتابیس به GitHub تا ربات تلگرام (GitHub Actions) خلاصه را بفرستد"
        )
        self.publish_btn.setStyleSheet(
            "QPushButton#PublishButton {"
            " background-color: rgba(99, 102, 241, 0.12);"
            " color: #6366f1;"
            " border: 1px solid rgba(99, 102, 241, 0.35);"
            " border-radius: 18px;"
            " padding: 8px 16px;"
            " font-weight: 600;"
            "}"
            "QPushButton#PublishButton:hover {"
            " background-color: rgba(99, 102, 241, 0.22);"
            "}"
            "QPushButton#PublishButton:pressed {"
            " background-color: rgba(99, 102, 241, 0.32);"
            "}"
            "QPushButton#PublishButton:disabled {"
            " color: rgba(120, 120, 130, 0.6);"
            " border-color: rgba(120, 120, 130, 0.25);"
            " background-color: transparent;"
            "}"
        )
        self.publish_btn.clicked.connect(self._on_publish_clicked_internal)
        layout.addWidget(self.publish_btn, alignment=Qt.AlignVCenter)

        # === ۳. دکمه‌ی گرد (چپ) ===
        self.circular_btn = PillProgressButton()
        self.circular_btn.button.clicked.connect(self.update_clicked.emit)
        layout.addWidget(self.circular_btn, alignment=Qt.AlignVCenter)

    def _on_publish_clicked_internal(self) -> None:
        """بازخورد لحظه‌ای روی دکمه و ارسال سیگنال."""
        if not self.publish_btn.isEnabled():
            return
        self._publish_default_text = "🚀 انتشار"
        self.publish_btn.setText("⏳ در حال ارسال...")
        self.publish_btn.setEnabled(False)
        self.publish_clicked.emit()

    # === Public API ===

    def set_publish_result(self, ok: bool, message: str = "") -> None:
        """نمایش نتیجه‌ی انتشار روی دکمه (۳ ثانیه) و بازگرداندن وضعیت."""
        from PySide6.QtCore import QTimer

        if ok:
            self.publish_btn.setText("✅ منتشر شد")
        else:
            self.publish_btn.setText("❌ خطا")
        if message:
            self.user_status.setText(message)

        default_text = getattr(self, "_publish_default_text", "🚀 انتشار")
        QTimer.singleShot(3000, lambda: self._restore_publish_button(default_text))

    def _restore_publish_button(self, text: str) -> None:
        self.publish_btn.setText(text)
        self.publish_btn.setEnabled(True)

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