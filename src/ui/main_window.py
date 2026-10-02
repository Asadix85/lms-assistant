"""پنجره اصلی LMS Assistant با Liquid Glass."""

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QMessageBox,
    QStatusBar,
    QApplication,
)

from config.settings import settings
from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import CourseRepository
from src.ui.header import Header
from src.ui.sidebar import Sidebar
from src.ui.theme import CurrentTheme, ThemeMode, get_global_qss
from src.ui.worker import SyncWorker
from src.ui.pages.about_page import AboutPage


class MainWindow(QMainWindow):
    """پنجره اصلی با Sidebar و صفحات."""

    DB_PATH = "data/lms.db"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LMS Assistant — دانشگاه اصفهان")
        self.resize(1300, 850)

        # ⚠️ شفاف کردن پنجره اصلی برای Acrylic Blur
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        self._thread: QThread | None = None
        self._worker: SyncWorker | None = None
        self._pages: dict[str, QWidget] = {}

        self._build_ui()
        self._load_data()
        self._update_user_name()
        self._enable_acrylic_blur()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setAttribute(Qt.WA_TranslucentBackground, True)
        central.setAttribute(Qt.WA_NoSystemBackground, True)
        central.setAutoFillBackground(False)
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        # ⚠️ theme_toggled حذف شد (به Settings منتقل شد)
        main_layout.addWidget(self.sidebar)

        # Content
        content = QWidget()
        content.setAttribute(Qt.WA_TranslucentBackground, True)
        content.setAttribute(Qt.WA_NoSystemBackground, True)
        content.setAutoFillBackground(False)

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
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content, stretch=1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")

    def _enable_acrylic_blur(self) -> None:
        """فعال‌سازی Acrylic Blur."""
        from src.ui.blur import enable_blur
        from src.ui.theme import CurrentTheme

        if CurrentTheme.is_dark():
            color = 0xFA0A0A0F
        else:
            color = 0xFAF8FAFC

        success = enable_blur(self, color=color, enable=True)
        if success:
            print(f"✅ Acrylic Blur فعال شد (tint: {hex(color)})")
        else:
            print("⚠️ Acrylic Blur پشتیبانی نمی‌شه")

    def _load_data(self) -> None:
        """بارگذاری صفحات."""
        from src.ui.pages.dashboard_page import DashboardPage
        from src.ui.pages.courses_page import CoursesPage
        from src.ui.pages.events_page import EventsPage
        from src.ui.pages.changes_page import ChangesPage
        from src.ui.pages.settings_page import SettingsPage
        from src.ui.pages.assignments_page import AssignmentsPage
        from src.ui.pages.course_detail_page import CourseDetailPage
        from src.ui.pages.calendar_page import CalendarPage

        # Dashboard
        self.dashboard_page = DashboardPage(self.DB_PATH)
        self._pages["dashboard"] = self.dashboard_page
        self.stack.addWidget(self.dashboard_page)

        # Calendar
        self.calendar_page = CalendarPage(self.DB_PATH)
        self._pages["calendar"] = self.calendar_page
        self.stack.addWidget(self.calendar_page)

        # Courses
        self.courses_page = CoursesPage(self.DB_PATH)
        self.courses_page.course_selected.connect(self._on_course_selected)
        self._pages["courses"] = self.courses_page
        self.stack.addWidget(self.courses_page)
        self.courses_page.sync_requested.connect(self._on_update_clicked)

        # Course Detail
        self.course_detail_page = CourseDetailPage(self.DB_PATH)
        self.course_detail_page.back_clicked.connect(
            lambda: self._on_page_changed("courses")
        )
        self._pages["course_detail"] = self.course_detail_page
        self.stack.addWidget(self.course_detail_page)

        # Assignments
        self.assignments_page = AssignmentsPage(self.DB_PATH)
        self._pages["assignments"] = self.assignments_page
        self.stack.addWidget(self.assignments_page)
        self.assignments_page.sync_requested.connect(self._on_update_clicked)

        # Events
        self.events_page = EventsPage(self.DB_PATH)
        self._pages["events"] = self.events_page
        self.stack.addWidget(self.events_page)

        # Changes
        self.changes_page = ChangesPage(self.DB_PATH)
        self._pages["changes"] = self.changes_page
        self.stack.addWidget(self.changes_page)
        self.changes_page.sync_requested.connect(self._on_update_clicked)

        # Settings
        self.settings_page = SettingsPage(self.DB_PATH)
        self._pages["settings"] = self.settings_page
        self.stack.addWidget(self.settings_page)

        # About
        self.about_page = AboutPage()
        self._pages["about"] = self.about_page
        self.stack.addWidget(self.about_page)

        self._update_user_name()

        self.stack.setCurrentWidget(self._pages["dashboard"])

    def _on_course_selected(self, course_id: str) -> None:
        try:
            with Database(self.DB_PATH) as db:
                course = CourseRepository(db).get_by_id(course_id)
                if course:
                    self.course_detail_page.load_course(course)
                    self.stack.setCurrentWidget(self.course_detail_page)
                    self.sidebar.set_active("courses")
                    self.status_bar.showMessage(f"درس: {course.name}")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری درس:\n{e}")

    def _on_page_changed(self, key: str) -> None:
        if key in self._pages:
            self.stack.setCurrentWidget(self._pages[key])
            page = self._pages[key]
            if hasattr(page, "refresh"):
                page.refresh()
            self.status_bar.showMessage(f"صفحه: {key}")

    # === Update ===

    def _on_update_clicked(self) -> None:
        if not settings.lms_username or not settings.lms_password:
            QMessageBox.warning(
                self, "خطا",
                "نام کاربری و رمز عبور در .env تنظیم نشده."
            )
            return

        self.header.set_busy(True, "در حال Sync...")
        self.status_bar.showMessage("🔄 در حال Sync...")

        self._thread = QThread()
        self._worker = SyncWorker(
            username=settings.lms_username,
            password=settings.lms_password,
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

    def _on_progress(self, message: str) -> None:
        self.header.set_busy(True, message)
        self.status_bar.showMessage(message)

    def _on_sync_finished(self, result: SyncResult) -> None:
        self.header.set_busy(False, "آماده")
        self.status_bar.showMessage("✅ Sync تمام شد")
        self._update_user_name()

        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

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

    def _update_user_name(self) -> None:
        """به‌روزرسانی نام کاربر در header."""
        try:
            with Database(self.DB_PATH) as db:
                from src.storage.repositories import SettingRepository
                name = SettingRepository(db).get("full_name")
                if name:
                    self.header.set_user(name)
        except Exception as e:
            print(f"خطا در به‌روزرسانی نام: {e}")

    def _on_sync_error(self, message: str) -> None:
        self.header.set_busy(False, "خطا")
        self.status_bar.showMessage(f"❌ خطا: {message}")
        QMessageBox.critical(self, "خطا در Sync", message)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None