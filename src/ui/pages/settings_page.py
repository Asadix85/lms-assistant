"""Settings Page: تنظیمات برنامه."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from config.settings import settings
from src.storage.database import Database
from src.storage.repositories import (
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)
from src.ui.pages.base_page import BasePage
from src.ui.theme import Colors, CurrentTheme
from src.ui.widgets.setting_card import SettingCard


class SettingsPage(BasePage):
    """صفحه‌ی تنظیمات."""

    settings_changed = Signal()
    theme_changed = Signal()

    def __init__(self, db_path: str, parent: QWidget | None = None) -> None:
        self.db_path = db_path
        super().__init__(
            title="تنظیمات",
            subtitle="پیکربندی برنامه",
            parent=parent,
        )
        self.refresh()

    def _build(self) -> None:
        super()._build()

        # === Scroll ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.scroll_widget)
        self.content_layout.addWidget(scroll, stretch=1)

        # === Cards ===
        self._build_user_card()
        self._build_sync_card()
        self._build_display_card()
        self._build_database_card()
        self._build_about_card()

    # === Cards ===

    def _build_user_card(self) -> None:
        card = SettingCard(title="اطلاعات کاربر", icon="👤")

        username = settings.lms_username or "—"
        card.add_row("نام کاربری", username)

        # آخرین Sync
        try:
            with Database(self.db_path) as db:
                setting_repo = SettingRepository(db)
                last_sync = setting_repo.get("last_sync_at", "—")
                first_sync = setting_repo.get("first_sync_done", "false")
        except Exception:
            last_sync = "—"
            first_sync = "false"

        if last_sync and last_sync != "—":
            last_sync = last_sync[:19].replace("T", " ")

        card.add_row("آخرین Sync", last_sync)
        card.add_row("اولین Sync", "✅ انجام شده" if first_sync == "true" else "❌ انجام نشده")

        # دامنه‌ها
        try:
            with Database(self.db_path) as db:
                course_repo = CourseRepository(db)
                courses = course_repo.get_all()
                domains = sorted(set(c.domain for c in courses))
                domains_str = ", ".join(domains) if domains else "—"
        except Exception:
            domains_str = "—"

        card.add_row("دامنه‌ها", domains_str)

        self.scroll_layout.addWidget(card)

    def _build_sync_card(self) -> None:
        card = SettingCard(title="تنظیمات Sync", icon="🔄")

        # چک‌باکس اعلان
        self.notify_checkbox = QCheckBox("نمایش اعلان پس از Sync")
        self.notify_checkbox.setChecked(True)
        card.add_widget(self.notify_checkbox)

        # چک‌باکس Sync خودکار
        self.auto_sync_checkbox = QCheckBox("Sync خودکار (در نسخه بعدی)")
        self.auto_sync_checkbox.setEnabled(False)
        card.add_widget(self.auto_sync_checkbox)

        self.scroll_layout.addWidget(card)

    def _build_display_card(self) -> None:
        card = SettingCard(title="نمایش", icon="🎨")

        # === Theme toggle ===
        c = CurrentTheme.colors()

        theme_row = QHBoxLayout()
        theme_row.setSpacing(10)

        theme_label = QLabel("تم برنامه:")
        theme_label.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent;"
        )
        theme_row.addWidget(theme_label)

        theme_row.addStretch()

        # ⚠️ دکمه‌ی تغییر تم
        from PySide6.QtWidgets import QPushButton
        self.theme_btn = QPushButton(
            "☀️  تم روشن" if CurrentTheme.is_dark() else "🌙  تم تیره"
        )
        self.theme_btn.setObjectName("SecondaryButton")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setMinimumWidth(160)
        self.theme_btn.clicked.connect(self._on_theme_toggle)
        theme_row.addWidget(self.theme_btn)

        container = QWidget()
        container.setLayout(theme_row)
        card.add_widget(container)

        self.scroll_layout.addWidget(card)

    def _on_theme_toggle(self) -> None:
        """تغییر تم برنامه."""
        from PySide6.QtWidgets import QApplication
        from src.ui.theme import CurrentTheme, ThemeMode, get_global_qss
        from src.ui.blur import enable_blur

        # toggle
        new_mode = (
            ThemeMode.DARK if not CurrentTheme.is_dark() else ThemeMode.LIGHT
        )
        CurrentTheme.set_mode(new_mode)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_global_qss(new_mode))

        # رنگ Acrylic
        main_window = self.window()
        if main_window:
            if CurrentTheme.is_dark():
                color = 0xFA0A0A0F
                self.theme_btn.setText("☀️  تم روشن")
            else:
                color = 0xFAF8FAFC
                self.theme_btn.setText("🌙  تم تیره")

            enable_blur(main_window, color=color, enable=True)

        self.refresh()
        self.theme_changed.emit()

    def _build_database_card(self) -> None:
        card = SettingCard(title="دیتابیس", icon="💾")

        # اندازه دیتابیس
        size_str = "—"
        db_path = Path(self.db_path)
        if db_path.exists():
            size = db_path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

        card.add_row("حجم", size_str)
        card.add_row("مسیر", str(db_path.absolute()))

        # دکمه‌ها
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        backup_btn = QPushButton("📦 بکاپ")
        backup_btn.setObjectName("SecondaryButton")
        backup_btn.clicked.connect(self._on_backup)
        btn_row.addWidget(backup_btn)

        clear_btn = QPushButton("🗑️ پاک کردن دیتابیس")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self._on_clear_db)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()

        container = QWidget()
        container.setLayout(btn_row)
        card.add_widget(container)

        self.scroll_layout.addWidget(card)

    def _build_about_card(self) -> None:
        card = SettingCard(title="درباره", icon="ℹ️")

        card.add_row("نسخه", "0.1.0")
        card.add_row("سازنده", "شخصی (برای دانشگاه اصفهان)")
        card.add_row("مخزن", "github.com/...")

        self.scroll_layout.addWidget(card)

    # === Data ===

    def refresh(self) -> None:
        """رفرش داده‌ها."""
        # پاک کردن
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # بازسازی
        self._build_user_card()
        self._build_sync_card()
        self._build_display_card()
        self._build_database_card()
        self._build_about_card()

    # === Events ===

    def _on_theme_changed(self, index: int) -> None:
        """تغییر تم."""
        if index == 1:
            QMessageBox.information(
                self,
                "به‌زودی",
                "تم تیره در نسخه بعدی اضافه می‌شود.",
            )
            self.theme_combo.setCurrentIndex(0)

    def _on_backup(self) -> None:
        """بکاپ دیتابیس."""
        src = Path(self.db_path)
        if not src.exists():
            QMessageBox.warning(self, "خطا", "دیتابیس پیدا نشد.")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره بکاپ",
            str(src.parent / "lms_backup.db"),
            "Database (*.db)",
        )
        if not dest:
            return

        import shutil
        try:
            shutil.copy2(src, dest)
            QMessageBox.information(
                self,
                "✅ موفق",
                f"بکاپ ذخیره شد:\n{dest}",
            )
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بکاپ:\n{e}")

    def _on_clear_db(self) -> None:
        """پاک کردن دیتابیس."""
        reply = QMessageBox.question(
            self,
            "🗑️ پاک کردن دیتابیس",
            "آیا مطمئن هستی؟ همه‌ی داده‌ها پاک می‌شوند.\n"
            "(بعد از پاک کردن، باید دوباره Sync بزنی.)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,  # ⚠️ پیش‌فرض No
        )
        if reply != QMessageBox.Yes:
            return

        db_path = Path(self.db_path)
        try:
            if db_path.exists():
                db_path.unlink()
            QMessageBox.information(self, "موفق", "دیتابیس پاک شد.")
            self.refresh()
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در پاک کردن:\n{e}")