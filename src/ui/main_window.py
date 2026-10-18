"""پنجره اصلی LMS Assistant — با System Tray و Sidebar راست."""
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QMessageBox,
    QStatusBar,
    QApplication,
    QBoxLayout,
    QSystemTrayIcon,
    QMenu,
)

from config.settings import settings
from src.services.settings_manager import SettingsManager
from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import CourseRepository
from src.ui.header import Header
from src.ui.sidebar import Sidebar
from src.ui.theme import CurrentTheme, ThemeMode, get_global_qss
from src.ui.worker import SyncWorker


class MainWindow(QMainWindow):
    """پنجره اصلی با Sidebar راست + System Tray."""

    @property
    def DB_PATH(self) -> str:
        from src.utils.paths import get_data_path
        return str(get_data_path("lms.db"))

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LMS Assistant — دانشگاه اصفهان")
        self.resize(1300, 850)

        # ⚠️ باگ قبلی: اتصال theme_changed داخل __init__ و قبل از ساخت
        # settings_page انجام می‌شد (هرگز اجرا نمی‌شد) و هندلر به‌صورت
        # تابع تو در تعریف شده بود. اتصال درست بعد از _load_data انجام می‌شود.

        # شفاف کردن پنجره
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        # آیکون پنجره
        from PySide6.QtGui import QIcon
        from pathlib import Path

        icon_path = Path("assets/icons/app.ico")
        if not icon_path.exists():
            icon_path = Path("assets/icons/app.png")

        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        from src.ui.icons import Icons
        Icons.clear_cache()

        self._thread: QThread | None = None
        self._worker: SyncWorker | None = None
        self._pages: dict[str, QWidget] = {}
        self._current_page_key: str = "dashboard"
        self._force_quit = False

        # ساخت UI
        self._build_ui()

        # RTL اولیه
        from src.ui.theme import apply_rtl_recursive
        apply_rtl_recursive(self.sidebar)
        apply_rtl_recursive(self.header)

        # بارگذاری صفحات
        self._load_data()

        # بازیابی geometry
        self._restore_geometry()

        # Acrylic blur
        self._enable_acrylic_blur()

        # System Tray
        self._setup_tray()

        # RTL دوباره بعد از نمایش
        QTimer.singleShot(100, self._apply_rtl_to_all)

    # ============================================================
    # System Tray
    # ============================================================

    def _setup_tray(self) -> None:
        """راه‌اندازی System Tray."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ System Tray در دسترس نیست")
            return

        self.tray = QSystemTrayIcon(self)

        # آیکون tray
        icon_path = Path("assets/icons/app.png")
        if icon_path.exists():
            self.tray.setIcon(QIcon(str(icon_path)))
        else:
            # fallback: آیکون پنجره
            self.tray.setIcon(self.windowIcon())

        self.tray.setToolTip("LMS Assistant — دانشگاه اصفهان")

        # === منو ===
        menu = QMenu()

        show_action = QAction("🏠  نمایش پنجره", self)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        sync_action = QAction("🔄  بروزرسانی ", self)
        sync_action.triggered.connect(self._on_update_clicked)
        menu.addAction(sync_action)

        menu.addSeparator()

        quit_action = QAction("❌  خروج", self)
        quit_action.triggered.connect(self._force_quit_app)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

        # === کلیک روی آیکون ===
        self.tray.activated.connect(self._on_tray_activated)

        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        """کلیک روی آیکون tray."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self._show_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self) -> None:
        """نمایش و فعال‌سازی پنجره."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _force_quit_app(self) -> None:
        """خروج واقعی از برنامه."""
        self._force_quit = True
        QApplication.quit()

    # ============================================================
    # UI
    # ============================================================

    def _apply_rtl_to_all(self) -> None:
        """اعمال RTL روی همه‌ی widgetها (بعد از نمایش)."""
        from src.ui.theme import apply_rtl_recursive

        for page in self._pages.values():
            apply_rtl_recursive(page)

        apply_rtl_recursive(self.sidebar)
        apply_rtl_recursive(self.header)

    def _build_ui(self) -> None:
        """ساخت UI با QGridLayout — Sidebar در ستون 0 (راست در RTL)."""
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setAttribute(Qt.WA_TranslucentBackground, True)
        central.setAttribute(Qt.WA_NoSystemBackground, True)
        central.setAutoFillBackground(False)
        central.setLayoutDirection(Qt.RightToLeft)
        self.setCentralWidget(central)

        # ⚠️ QGridLayout — دقیقاً کنترل می‌کنیم کدوم سمت
        # در RTL: ستون 0 = راست، ستون 1 = چپ
        grid = QGridLayout(central)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        # === Sidebar در ستون 0 (راست در RTL) ===
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        grid.addWidget(self.sidebar, 0, 0)

        # === Content در ستون 1 (چپ در RTL) ===
        content = QWidget()
        content.setAttribute(Qt.WA_TranslucentBackground, True)
        content.setAttribute(Qt.WA_NoSystemBackground, True)
        content.setAutoFillBackground(False)
        content.setLayoutDirection(Qt.RightToLeft)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = Header()
        self.header.update_clicked.connect(self._on_update_clicked)
        content_layout.addWidget(self.header)

        # Stack
        self.stack = QStackedWidget()
        self.stack.setAttribute(Qt.WA_TranslucentBackground, True)
        self.stack.setAutoFillBackground(False)
        self.stack.setLayoutDirection(Qt.RightToLeft)
        content_layout.addWidget(self.stack)

        grid.addWidget(content, 0, 1)

        # ستون 1 (محتوا) کشیده بشه، ستون 0 (سایدبار) ثابت
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(0, 0)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")

    def _enable_acrylic_blur(self) -> None:
        """فعال‌سازی Acrylic Blur."""
        from src.ui.blur import enable_blur

        if CurrentTheme.is_dark():
            color = 0xFA0A0A0F
        else:
            color = 0xFAF8FAFC

        enable_blur(self, color=color, enable=True)

    def _load_data(self) -> None:
        """بارگذاری صفحات."""
        # ⚠️ مهم: init_schema قبل از همه چیز
        print(f"📂 DB_PATH: {self.DB_PATH}")

        from src.storage.database import Database
        try:
            with Database(self.DB_PATH) as db:
                db.init_schema()
            print(f"✅ Schema آماده: {self.DB_PATH}")
        except Exception as e:
            print(f"❌ خطا در init_schema: {e}")

        from src.ui.pages.dashboard_page import DashboardPage
        from src.ui.pages.courses_page import CoursesPage
        from src.ui.pages.events_page import EventsPage
        from src.ui.pages.changes_page import ChangesPage
        from src.ui.pages.settings_page import SettingsPage
        from src.ui.pages.assignments_page import AssignmentsPage
        from src.ui.pages.course_detail_page import CourseDetailPage
        from src.ui.pages.calendar_page import CalendarPage
        from src.ui.pages.about_page import AboutPage
        from src.ui.pages.analytics_page import AnalyticsPage

        # === Dashboard ===
        self.dashboard_page = DashboardPage(self.DB_PATH)
        self.dashboard_page.course_selected.connect(self._on_course_selected)
        self._pages["dashboard"] = self.dashboard_page
        self.stack.addWidget(self.dashboard_page)

        # === Calendar ===
        self.calendar_page = CalendarPage(self.DB_PATH)
        self._pages["calendar"] = self.calendar_page
        self.stack.addWidget(self.calendar_page)

        # === Courses ===
        self.courses_page = CoursesPage(self.DB_PATH)
        self.courses_page.course_selected.connect(self._on_course_selected)
        self.courses_page.sync_requested.connect(self._on_update_clicked)
        self._pages["courses"] = self.courses_page
        self.stack.addWidget(self.courses_page)

        # === Course Detail ===
        self.course_detail_page = CourseDetailPage(self.DB_PATH)
        self.course_detail_page.back_clicked.connect(
            lambda: self._on_page_changed("courses")
        )
        self._pages["course_detail"] = self.course_detail_page
        self.stack.addWidget(self.course_detail_page)

        # === Assignments ===
        self.assignments_page = AssignmentsPage(self.DB_PATH)
        self.assignments_page.sync_requested.connect(self._on_update_clicked)
        self._pages["assignments"] = self.assignments_page
        self.stack.addWidget(self.assignments_page)

        # === Events ===
        self.events_page = EventsPage(self.DB_PATH)
        self._pages["events"] = self.events_page
        self.stack.addWidget(self.events_page)

        # === Analytics ===  ← ⚠️ این بخش جدید
        self.analytics_page = AnalyticsPage(self.DB_PATH)
        self._pages["analytics"] = self.analytics_page
        self.stack.addWidget(self.analytics_page)

        # === Changes ===
        self.changes_page = ChangesPage(self.DB_PATH)
        self.changes_page.sync_requested.connect(self._on_update_clicked)
        self._pages["changes"] = self.changes_page
        self.stack.addWidget(self.changes_page)

        # === Settings ===
        self.settings_page = SettingsPage(self.DB_PATH)
        self._pages["settings"] = self.settings_page
        self.stack.addWidget(self.settings_page)

        # === About ===
        self.about_page = AboutPage()
        self._pages["about"] = self.about_page
        self.stack.addWidget(self.about_page)

        # ✅ اتصال صحیح سیگنال تغییر تم (بعد از ساخت صفحات)
        self.settings_page.theme_changed.connect(self._on_theme_changed)

        # بازیابی آخرین صفحه
        last_page = SettingsManager.load_last_page(default="dashboard")
        if last_page in self._pages:
            self._current_page_key = last_page
            self.stack.setCurrentWidget(self._pages[last_page])
            self.sidebar.set_active(last_page)
        else:
            self.stack.setCurrentWidget(self._pages["dashboard"])

    def _restore_geometry(self) -> None:
        """بازیابی اندازه و موقعیت پنجره."""
        geometry_bytes = SettingsManager.load_geometry()
        if geometry_bytes:
            try:
                self.restoreGeometry(geometry_bytes)
                print("✅ اندازه پنجره بازیابی شد")
            except Exception as e:
                print(f"⚠️ خطا در بازیابی geometry: {e}")

    # ============================================================
    # Events
    # ============================================================

    def closeEvent(self, event) -> None:
        """ذخیره‌ی تنظیمات هنگام بستن پنجره."""
        try:
            SettingsManager.save_geometry(self.saveGeometry().data())
            SettingsManager.save_theme(CurrentTheme.mode)
            SettingsManager.save_last_page(self._current_page_key)
            print("💾 تنظیمات ذخیره شد")
        except Exception as e:
            print(f"⚠️ خطا در ذخیره تنظیمات: {e}")

        super().closeEvent(event)  # ← بستن عادی

    def _on_course_selected(self, course_id: str) -> None:
        try:
            with Database(self.DB_PATH) as db:
                course = CourseRepository(db).get_by_id(course_id)
                if course:
                    self.course_detail_page.load_course(course)
                    self.stack.setCurrentWidget(self.course_detail_page)
                    self._current_page_key = "courses"
                    self.sidebar.set_active("courses")
                    self.status_bar.showMessage(f"درس: {course.name}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری درس:\n{e}")

    def _on_page_changed(self, key: str) -> None:
        if key in self._pages:
            self.stack.setCurrentWidget(self._pages[key])
            self._current_page_key = key
            page = self._pages[key]
            if hasattr(page, "refresh"):
                page.refresh()
            self.status_bar.showMessage(f"صفحه: {key}")

    # ============================================================
    # Update / Sync
    # ============================================================

    def _on_update_clicked(self) -> None:
        print("🔘 دکمه‌ی Sync کلیک شد!")

        from src.services.credential_provider import CredentialProvider

        creds = CredentialProvider.get()

        print(f"🔍 lms_username: {bool(creds.lms_username)}")
        print(f"🔍 lms_password: {bool(creds.lms_password)}")

        has_lms = bool(creds.lms_username and creds.lms_password)
        has_quera = bool(creds.quera_username and creds.quera_password)

        if not has_lms and not has_quera:
            print("❌ credentials نیست — Dialog باز می‌شه")
            self._show_login_dialog()
            return

        print(f"✅ شروع Sync برای {creds.lms_username}")

        self.header.set_busy(True, "در حال Sync...")
        self.status_bar.showMessage("🔄 در حال Sync...")

        self._thread = QThread()
        self._worker = SyncWorker(
            username=creds.lms_username,  # ← از creds
            password=creds.lms_password,
            db_path=self.DB_PATH,
            notify=True,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

    def _show_login_dialog(self) -> None:
        """باز کردن Dialog ورود."""
        from src.services.credential_provider import CredentialProvider
        from src.ui.dialogs.login_dialog import LoginDialog

        creds = CredentialProvider.get()

        dialog = LoginDialog(
            self,
            lms_username=creds.lms_username,
            lms_password=creds.lms_password,
            quera_username=creds.quera_username,
            quera_password=creds.quera_password,
        )

        dialog.login_success.connect(
            lambda lu, lp, qu, qp: CredentialProvider.update(lu, lp, qu, qp)
        )

        if dialog.exec() == LoginDialog.Accepted:
            self.status_bar.showMessage("✅ اطلاعات ذخیره شد")

    def _on_progress(self, progress) -> None:
        """دریافت progress از worker."""
        from src.services.sync_progress import SyncProgress

        if not isinstance(progress, SyncProgress):
            return

        self.header.set_progress(progress)

        status_text = progress.message
        if progress.changes_text:
            status_text += f"  |  {progress.changes_text}"
        if progress.elapsed > 0:
            status_text += f"  |  ⏱️ {progress.elapsed_text}"
        self.status_bar.showMessage(status_text)

    # ============================================================
    # Theme
    # ============================================================

    def _on_theme_changed(self) -> None:
        """بعد از تغییر تم از settings page."""
        self.refresh_all_pages_theme()
        self._apply_rtl_to_all()

    def refresh_all_pages_theme(self) -> None:
        """بعد از تغییر تم، همه صفحات رو به‌روز کن.

        ⚠️ باگ قبلی: این متد داخل یک کلاس MainWindow تودرتو تعریف شده بود
        که باعث می‌شد نسخه‌ی اصلی کلاس این متد را نداشته باشد و فراخوانی آن
        با AttributeError یا skip کامل مواجه شود.
        """
        for page in self._pages.values():
            if hasattr(page, "refresh_theme"):
                try:
                    page.refresh_theme()
                except Exception as e:  # noqa: BLE001
                    print(f"⚠️ خطا در refresh_theme صفحه‌ی {type(page).__name__}: {e}")

    def _on_sync_finished(self, result: SyncResult) -> None:
        self.header.set_busy(False, "آماده")
        self.status_bar.showMessage("✅ Sync تمام شد")

        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

        # اعلان tray
        if hasattr(self, "tray") and self.tray.isVisible():
            if result.has_error:
                self.tray.showMessage(
                    "❌ خطا در Sync",
                    result.error or "خطای نامشخص",
                    QSystemTrayIcon.MessageIcon.Critical,
                    3000,
                )
            elif result.total_new > 0:
                self.tray.showMessage(
                    "📢 تغییرات جدید",
                    f"{result.total_new} آیتم جدید",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )

        if result.has_error:
            QMessageBox.critical(self, "خطا", f"خطا در Sync:\n{result.error}")
        elif result.is_first_sync:
            QMessageBox.information(
                self, "اولین Sync",
                f"🎉 اولین Sync موفق!\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n"
                f"📢 {result.posts_new} پیام\n"
                f"📋 {result.assignments_new} تکلیف\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )
        elif result.total_new == 0:
            QMessageBox.information(
                self, "بدون تغییر",
                f"✨ هیچ تغییر جدیدی نیست\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )
        else:
            QMessageBox.information(
                self, "تغییرات جدید",
                f"📢 تغییرات جدید:\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n"
                f"📢 {result.posts_new} پیام\n"
                f"📋 {result.assignments_new} تکلیف\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )

    def _on_sync_error(self, message: str) -> None:
        self.header.set_busy(False, "خطا")
        self.status_bar.showMessage(f"❌ خطا: {message}")
        QMessageBox.critical(self, "خطا در Sync", message)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None

    def showEvent(self, event) -> None:
        """بعد از نمایش پنجره، RTL رو اعمال کن."""
        super().showEvent(event)
        QTimer.singleShot(50, self._apply_rtl_to_all)