"""پنجره اصلی LMS Assistant (نسخه جدید با Sidebar)."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QMessageBox,
    QStatusBar,
)

from config.settings import settings
from src.services.sync_result import SyncResult
from src.ui.header import Header
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.sidebar import Sidebar
from src.ui.worker import SyncWorker


class MainWindow(QMainWindow):
    """پنجره اصلی با Sidebar و صفحات."""

    DB_PATH = "data/lms.db"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LMS Assistant — دانشگاه اصفهان")
        self.resize(1200, 800)

        self._thread: QThread | None = None
        self._worker: SyncWorker | None = None
        self._pages: dict[str, QWidget] = {}

        self._build_ui()
        self._apply_rtl()
        self._load_data()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        # === Main Layout ===
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === Sidebar (Right in RTL) ===
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self.sidebar)

        # === Main Content ===
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = Header()
        self.header.update_clicked.connect(self._on_update_clicked)
        content_layout.addWidget(self.header)

        # Pages (Stacked)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content, stretch=1)

        # === Status Bar ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")

    def _apply_rtl(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft)

    def _load_data(self) -> None:
        """بارگذاری صفحات."""
        from src.ui.pages.courses_page import CoursesPage
        from src.ui.pages.events_page import EventsPage

        # Dashboard
        self.dashboard_page = DashboardPage(self.DB_PATH)
        self._pages["dashboard"] = self.dashboard_page
        self.stack.addWidget(self.dashboard_page)

        # Courses
        self.courses_page = CoursesPage(self.DB_PATH)
        self.courses_page.course_selected.connect(self._on_course_selected)
        self._pages["courses"] = self.courses_page
        self.stack.addWidget(self.courses_page)

        # Events
        self.events_page = EventsPage(self.DB_PATH)
        self._pages["events"] = self.events_page
        self.stack.addWidget(self.events_page)

        # Placeholder pages
        for key, title in [
            ("changes", "تغییرات"),
            ("settings", "تنظیمات"),
        ]:
            from src.ui.pages.base_page import BasePage
            page = BasePage(title=title, subtitle="به‌زودی...")
            self._pages[key] = page
            self.stack.addWidget(page)

        self.stack.setCurrentWidget(self._pages["dashboard"])

    def _on_course_selected(self, course_id: str) -> None:
        """کلیک روی یک درس."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "درس انتخاب شد",
            f"Course ID: {course_id}\n\n(جزئیات در Phase بعدی)",
        )

    def _on_page_changed(self, key: str) -> None:
        """تغییر صفحه."""
        if key in self._pages:
            self.stack.setCurrentWidget(self._pages[key])
            # رفرش صفحه
            page = self._pages[key]
            if hasattr(page, "refresh"):
                page.refresh()
            self.status_bar.showMessage(f"صفحه: {key}")

    def _on_update_clicked(self) -> None:
        """دکمه Update."""
        if not settings.lms_username or not settings.lms_password:
            QMessageBox.warning(self, "خطا", "نام کاربری و رمز عبور در .env تنظیم نشده.")
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

        # رفرش dashboard
        if hasattr(self.dashboard_page, "refresh"):
            self.dashboard_page.refresh()

        # نمایش نتیجه
        if result.has_error:
            QMessageBox.critical(self, "خطا", f"خطا در Sync:\n{result.error}")
        elif result.is_first_sync:
            QMessageBox.information(
                self, "اولین Sync",
                f"🎉 اولین Sync موفق!\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n\n"
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
                f"📅 {result.events_new} رویداد\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )

    def _on_sync_error(self, message: str) -> None:
        self.header.set_busy(False, "خطا")
        self.status_bar.showMessage(f"❌ خطا: {message}")
        QMessageBox.critical(self, "خطا در Sync", message)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None