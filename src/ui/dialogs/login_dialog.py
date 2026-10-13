"""Login Dialog: ورود LMS + Quera."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QCheckBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from src.services.credentials_manager import CredentialsManager
from src.ui.theme import CurrentTheme


class LoginDialog(QDialog):
    """دیالوگ ورود LMS + Quera."""

    login_success = Signal(str, str, str, str)  # lms_u, lms_p, quera_u, quera_p

    def __init__(
        self,
        parent=None,
        lms_username: str = "",
        lms_password: str = "",
        quera_username: str = "",
        quera_password: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("ورود به LMS Assistant")
        self.setMinimumWidth(480)
        self.setModal(True)

        # آیکون
        from pathlib import Path
        icon_path = Path("assets/icons/app.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._build()

        # پر کردن مقادیر پیش‌فرض
        self.lms_username_input.setText(lms_username)
        self.lms_password_input.setText(lms_password)
        self.quera_username_input.setText(quera_username)
        self.quera_password_input.setText(quera_password)

    def _build(self) -> None:
        c = CurrentTheme.colors()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # === Header ===
        title = QLabel("🎓  LMS Assistant")
        title.setStyleSheet(
            f"color: {c.PRIMARY}; font-size: 20pt; font-weight: bold; "
            "background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("برای شروع، اطلاعات ورود خود را وارد کنید")
        subtitle.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 11pt; "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # ============================================
        # LMS Section
        # ============================================
        lms_card = QFrame()
        lms_card.setObjectName("Card")
        lms_layout = QVBoxLayout(lms_card)
        lms_layout.setContentsMargins(20, 16, 20, 16)
        lms_layout.setSpacing(10)

        lms_title = QLabel("📚  LMS دانشگاه اصفهان")
        lms_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent;"
        )
        lms_title.setAlignment(Qt.AlignRight)
        lms_layout.addWidget(lms_title)

        # Username
        self.lms_username_input = QLineEdit()
        self.lms_username_input.setPlaceholderText("شماره دانشجویی (مثلاً 4043613005)")
        self.lms_username_input.setMinimumHeight(40)
        self.lms_username_input.setAlignment(Qt.AlignRight)
        lms_layout.addWidget(self.lms_username_input)

        # Password
        self.lms_password_input = QLineEdit()
        self.lms_password_input.setPlaceholderText("رمز عبور LMS")
        self.lms_password_input.setEchoMode(QLineEdit.Password)
        self.lms_password_input.setMinimumHeight(40)
        self.lms_password_input.setAlignment(Qt.AlignRight)
        lms_layout.addWidget(self.lms_password_input)

        layout.addWidget(lms_card)

        # ============================================
        # Quera Section (اختیاری)
        # ============================================
        quera_card = QFrame()
        quera_card.setObjectName("Card")
        quera_layout = QVBoxLayout(quera_card)
        quera_layout.setContentsMargins(20, 16, 20, 16)
        quera_layout.setSpacing(10)

        quera_title = QLabel("🎯  Quera (اختیاری)")
        quera_title.setStyleSheet(
            f"color: {c.TEXT_PRIMARY}; font-weight: bold; font-size: 13pt; "
            "background: transparent;"
        )
        quera_title.setAlignment(Qt.AlignRight)
        quera_layout.addWidget(quera_title)

        # Username
        self.quera_username_input = QLineEdit()
        self.quera_username_input.setPlaceholderText("ایمیل Quera")
        self.quera_username_input.setMinimumHeight(40)
        self.quera_username_input.setAlignment(Qt.AlignRight)
        quera_layout.addWidget(self.quera_username_input)

        # Password
        self.quera_password_input = QLineEdit()
        self.quera_password_input.setPlaceholderText("رمز عبور Quera")
        self.quera_password_input.setEchoMode(QLineEdit.Password)
        self.quera_password_input.setMinimumHeight(40)
        self.quera_password_input.setAlignment(Qt.AlignRight)
        quera_layout.addWidget(self.quera_password_input)

        layout.addWidget(quera_card)

        # === Remember Me ===
        self.remember_check = QCheckBox("💾  ذخیره‌ی رمز عبور (Remember Me)")
        self.remember_check.setChecked(True)
        self.remember_check.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.remember_check)

        layout.addSpacing(10)

        # === Buttons ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.login_btn = QPushButton("🚀  ورود به برنامه")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.setMinimumHeight(46)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login)
        btn_row.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setObjectName("SecondaryButton")
        self.cancel_btn.setMinimumHeight(46)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        layout.addLayout(btn_row)

        # === Hint ===
        hint = QLabel(
            "💡 اطلاعات شما به‌صورت امن در Windows Credential Manager ذخیره می‌شود."
        )
        hint.setStyleSheet(
            f"color: {c.TEXT_MUTED}; font-size: 9pt; "
            "background: transparent; padding-top: 8px;"
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def _on_login(self) -> None:
        """بررسی و ذخیره‌ی اطلاعات."""
        lms_u = self.lms_username_input.text().strip()
        lms_p = self.lms_password_input.text().strip()
        quera_u = self.quera_username_input.text().strip()
        quera_p = self.quera_password_input.text().strip()

        # === اعتبارسنجی ===
        if not lms_u or not lms_p:
            QMessageBox.warning(
                self, "خطا",
                "لطفاً اطلاعات LMS (شماره دانشجویی و رمز عبور) را وارد کنید."
            )
            return

        # Quera اگه یکی وارد شد، هر دو لازمه
        if (quera_u and not quera_p) or (not quera_u and quera_p):
            QMessageBox.warning(
                self, "خطا",
                "برای Quera، هم ایمیل و هم رمز عبور را وارد کنید (یا هر دو را خالی بگذارید)."
            )
            return

        # === ذخیره در keyring ===
        if self.remember_check.isChecked():
            CredentialsManager.save_lms(lms_u, lms_p)
            if quera_u and quera_p:
                CredentialsManager.save_quera(quera_u, quera_p)

        # === Emit signal ===
        self.login_success.emit(lms_u, lms_p, quera_u, quera_p)
        self.accept()