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
from src.ui.widgets.check_box import CustomCheckBox


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
        from src.services.settings_manager import SettingsManager
        from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

        card = SettingCard(title="تنظیمات Sync", icon="🔄")
        c = CurrentTheme.colors()

        # === عنوان توضیحی ===
        info = QLabel(
            "انتخاب کنید چه چیزهایی از LMS دریافت شوند.\n"
            "کمتر انتخاب کنید → سریع‌تر Sync می‌شه."
        )
        info.setStyleSheet(
            f"color: {c.TEXT_SECONDARY}; font-size: 10pt; "
            "background: transparent; padding: 5px 0;"
        )
        info.setWordWrap(True)
        card.add_widget(info)

        # === چک‌باکس‌ها ===
        settings = SettingsManager.get_sync_settings()

        self.sync_checkboxes = {}

        # دروس (اجباری)
        cb_courses = CustomCheckBox("📚  دروس (اجباری)")
        cb_courses.setChecked(True)
        cb_courses.setEnabled(False)
        self.sync_checkboxes["courses"] = cb_courses
        card.add_widget(cb_courses)

        # محتوا
        cb_contents = CustomCheckBox("📄  فایل‌ها و محتوای دروس")
        cb_contents.setChecked(settings.get("contents", True))
        self.sync_checkboxes["contents"] = cb_contents
        card.add_widget(cb_contents)

        # رویدادها
        cb_events = CustomCheckBox("📅  رویدادها (جلسات آنلاین)")
        cb_events.setChecked(settings.get("events", True))
        self.sync_checkboxes["events"] = cb_events
        card.add_widget(cb_events)

        # wall
        cb_wall = CustomCheckBox("📢  پیام‌ها و تکالیف (wall)")
        cb_wall.setChecked(settings.get("wall", True))
        self.sync_checkboxes["wall"] = cb_wall
        card.add_widget(cb_wall)

        # همکلاسی‌ها
        cb_members = CustomCheckBox("👥  همکلاسی‌ها (کند)")
        cb_members.setChecked(settings.get("members", False))
        self.sync_checkboxes["members"] = cb_members
        card.add_widget(cb_members)

        # === زمان تقریبی ===
        self.time_label = QLabel("")
        self.time_label.setStyleSheet(
            f"color: {c.PRIMARY}; font-weight: bold; font-size: 12pt; "
            "background: transparent; padding: 12px 0 4px 0;"
        )
        self.time_label.setAlignment(Qt.AlignRight)
        card.add_widget(self.time_label)

        self._update_time_estimate()

        # وصل کردن تغییرات
        for cb in self.sync_checkboxes.values():
            cb.toggled.connect(self._on_sync_option_changed)

        self.scroll_layout.addWidget(card)

        # وصل کردن تغییرات
        for cb in self.sync_checkboxes.values():
            cb.toggled.connect(self._on_sync_option_changed)

        self.scroll_layout.addWidget(card)

    def _on_sync_option_changed(self, checked: bool = False) -> None:
        """ذخیره‌ی تنظیمات جدید + آپدیت زمان."""
        from src.services.settings_manager import SettingsManager

        settings = {
            key: cb.isChecked()
            for key, cb in self.sync_checkboxes.items()
        }
        SettingsManager.save_sync_settings(settings)
        self._update_time_estimate()

    def _add_separator(self, layout) -> None:
        from PySide6.QtWidgets import QFrame
        from src.ui.theme import CurrentTheme
        c = CurrentTheme.colors()

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"background-color: {c.BORDER_LIGHT}; max-height: 1px;"
        )
        layout.addWidget(sep)

    def _on_sync_option_changed(self) -> None:
        """ذخیره‌ی تنظیمات جدید + آپدیت زمان."""
        from src.services.settings_manager import SettingsManager

        settings = {
            key: cb.isChecked()
            for key, cb in self.sync_checkboxes.items()
        }
        SettingsManager.save_sync_settings(settings)
        self._update_time_estimate()

    def _update_time_estimate(self) -> None:
        """محاسبه‌ی زمان تقریبی Sync (بر اساس لاگ‌های واقعی)."""
        settings = {
            key: cb.isChecked()
            for key, cb in self.sync_checkboxes.items()
        }

        # ⚠️ زمان‌های واقعی (از لاگ‌های اخیر):
        # login + courses = 8s
        # contents = 7s
        # events = 0.8s
        # wall = 6.5s
        # members = 19s (متوسط)

        time = 8  # login + courses (اجباری)
        if settings.get("contents"):
            time += 7
        if settings.get("events"):
            time += 1
        if settings.get("wall"):
            time += 7
        if settings.get("members"):
            time += 19  # ← دقیق‌تر شد (قبلاً 25 بود)

        # نمایش
        if time > 90:
            minutes = time // 60
            seconds = time % 60
            text = f"~{minutes} دقیقه و {seconds} ثانیه"
        else:
            text = f"~{time} ثانیه"

        # ⚠️ اگه فقط دروس → سریع
        if time == 8:
            text = "~8 ثانیه (سریع‌ترین)"

        self.time_label.setText(f"⏱️  زمان تقریبی: {text}")

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
        from PySide6.QtCore import QTimer
        from src.ui.theme import (
            CurrentTheme, ThemeMode, get_global_qss, apply_rtl_recursive,
        )
        from src.ui.icons import Icons
        from src.ui.blur import enable_blur
        from src.services.settings_manager import SettingsManager

        # ۱. تغییر تم
        new_mode = (
            ThemeMode.DARK if not CurrentTheme.is_dark() else ThemeMode.LIGHT
        )
        CurrentTheme.set_mode(new_mode)
        SettingsManager.save_theme(new_mode)

        # ۲. پاک کردن کش آیکون‌ها
        Icons.clear_cache()

        # ۳. اعمال QSS جدید
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_global_qss(new_mode))

        # ۴. رنگ Acrylic
        main_window = self.window()
        if main_window:
            if CurrentTheme.is_dark():
                color = 0xFA0A0A0F
                self.theme_btn.setText("☀️  تم روشن")
            else:
                color = 0xFAF8FAFC
                self.theme_btn.setText("🌙  تم تیره")

            enable_blur(main_window, color=color, enable=True)

            # ۵. رفرش Sidebar (آیکون‌ها)
            if hasattr(main_window, "sidebar"):
                main_window.sidebar.refresh_icons()

        # ۶. رفرش خود Settings
        self.refresh()

        # ۷. ⚠️ RTL با تأخیر کوتاه (بعد از رندر QSS جدید)
        if main_window:
            QTimer.singleShot(50, lambda: self._apply_rtl_to_window(main_window))

    def _apply_rtl_to_window(self, window) -> None:
        """اعمال RTL روی پنجره و همه‌ی صفحات."""
        from src.ui.theme import apply_rtl_recursive

        apply_rtl_recursive(window)

        if hasattr(window, "sidebar"):
            apply_rtl_recursive(window.sidebar)
        if hasattr(window, "header"):
            apply_rtl_recursive(window.header)
        if hasattr(window, "stack"):
            current = window.stack.currentWidget()
            if current:
                apply_rtl_recursive(current)

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