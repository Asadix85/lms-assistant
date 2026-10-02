"""پنجره اصلی LMS Assistant."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QSize
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QStatusBar,
    QProgressBar,
    QFrame,
)

from config.settings import settings
from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import (
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)
from src.ui.worker import SyncWorker


class MainWindow(QMainWindow):
    """پنجره اصلی برنامه."""

    DB_PATH = "data/lms.db"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LMS Assistant — دانشگاه اصفهان")
        self.resize(1000, 700)

        # Thread
        self._thread: QThread | None = None
        self._worker: SyncWorker | None = None

        self._build_ui()
        self._apply_rtl()
        self._load_initial_data()

    # === UI ===

    def _build_ui(self) -> None:
        """ساخت رابط کاربری."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # === Header ===
        header = self._build_header()
        layout.addWidget(header)

        # === Update button ===
        self.update_btn = QPushButton("🔄  بروزرسانی از LMS")
        self.update_btn.setMinimumHeight(50)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.update_btn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self.update_btn)

        # === Progress bar ===
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # === Tabs ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; }
            QTabBar::tab { padding: 8px 20px; font-size: 13px; }
            QTabBar::tab:selected { background: #3498db; color: white; }
        """)

        self.courses_table = self._build_courses_table()
        self.events_table = self._build_events_table()
        self.changes_table = self._build_changes_table()

        self.tabs.addTab(self.courses_table, "📚 دروس")
        self.tabs.addTab(self.events_table, "📅 رویدادها")
        self.tabs.addTab(self.changes_table, "🔔 تغییرات")

        layout.addWidget(self.tabs)

        # === Status bar ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")

    def _build_header(self) -> QWidget:
        """ساخت هدر."""
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(header)

        # عنوان
        title = QLabel("🎓  LMS Assistant")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # User info
        self.user_label = QLabel("وارد نشده")
        self.user_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        layout.addWidget(self.user_label)

        return header

    def _build_courses_table(self) -> QTableWidget:
        """جدول دروس."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "نام درس", "استاد", "کد", "دامنه"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _build_events_table(self) -> QTableWidget:
        """جدول رویدادها."""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["#", "عنوان", "ساعت", "لینک"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _build_changes_table(self) -> QTableWidget:
        """جدول تغییرات."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "نوع", "موجودیت", "ID", "زمان"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table

    def _apply_rtl(self) -> None:
        """اعمال راست‌چین."""
        self.setLayoutDirection(Qt.RightToLeft)

    # === Data Loading ===

    def _load_initial_data(self) -> None:
        """بارگذاری داده‌های اولیه از دیتابیس."""
        try:
            with Database(self.DB_PATH) as db:
                db.init_schema()
                self._load_courses(db)
                self._load_events(db)
                self._load_changes(db)
                self._update_status(db)
        except Exception as e:
            self.status_bar.showMessage(f"خطا در بارگذاری: {e}")

    def _load_courses(self, db: Database) -> None:
        repo = CourseRepository(db)
        courses = repo.get_all()
        self.courses_table.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self.courses_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.courses_table.setItem(i, 1, QTableWidgetItem(c.name))
            self.courses_table.setItem(i, 2, QTableWidgetItem(c.teacher or "—"))
            self.courses_table.setItem(i, 3, QTableWidgetItem(c.code or "—"))
            domain_icon = {"lms3": "🟢", "lms4": "🔵", "lms5": "🔴"}.get(c.domain, "⚪")
            self.courses_table.setItem(i, 4, QTableWidgetItem(f"{domain_icon} {c.domain}"))

    def _load_events(self, db: Database) -> None:
        repo = EventRepository(db)
        events = repo.get_all()
        self.events_table.setRowCount(len(events))
        for i, e in enumerate(events):
            self.events_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.events_table.setItem(i, 1, QTableWidgetItem(e.title))
            time_str = e.start_at.strftime("%H:%M") if e.start_at else "—"
            self.events_table.setItem(i, 2, QTableWidgetItem(time_str))
            url_short = (e.url[:50] + "...") if e.url and len(e.url) > 50 else (e.url or "—")
            self.events_table.setItem(i, 3, QTableWidgetItem(url_short))

    def _load_changes(self, db: Database) -> None:
        repo = ChangeRepository(db)
        changes = repo.get_recent(limit=50)
        self.changes_table.setRowCount(len(changes))
        for i, c in enumerate(changes):
            self.changes_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.changes_table.setItem(i, 1, QTableWidgetItem(c.type.value))
            self.changes_table.setItem(i, 2, QTableWidgetItem(c.entity_type.value))
            self.changes_table.setItem(i, 3, QTableWidgetItem(c.entity_id[:20]))
            self.changes_table.setItem(i, 4, QTableWidgetItem(
                c.detected_at.strftime("%Y-%m-%d %H:%M")
            ))

    def _update_status(self, db: Database) -> None:
        course_count = CourseRepository(db).count()
        event_count = EventRepository(db).count()
        setting_repo = SettingRepository(db)
        last_sync = setting_repo.get("last_sync_at", "—")

        if last_sync != "—":
            last_sync = last_sync[:19].replace("T", " ")

        self.status_bar.showMessage(
            f"📚 {course_count} درس  |  📅 {event_count} رویداد  |  🔄 آخرین Sync: {last_sync}"
        )

    # === Sync ===

    def _on_update_clicked(self) -> None:
        """دکمه بروزرسانی."""
        # چک کردن اعتبارنامه
        if not settings.lms_username or not settings.lms_password:
            QMessageBox.warning(
                self,
                "خطا",
                "نام کاربری و رمز عبور در .env تنظیم نشده.",
            )
            return

        # غیرفعال کردن دکمه
        self.update_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_bar.showMessage("در حال Sync...")

        # Thread + Worker
        self._thread = QThread()
        self._worker = SyncWorker(
            username=settings.lms_username,
            password=settings.lms_password,
            db_path=self.DB_PATH,
        )
        self._worker.moveToThread(self._thread)

        # Signals
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

    def _on_progress(self, message: str) -> None:
        self.status_bar.showMessage(message)

    def _on_sync_finished(self, result: SyncResult) -> None:
        self.progress.setVisible(False)
        self.update_btn.setEnabled(True)

        # Reload data
        self._load_initial_data()

        # Show result
        if result.has_error:
            QMessageBox.critical(self, "خطا", f"خطا در Sync:\n{result.error}")
        elif result.is_first_sync:
            QMessageBox.information(
                self,
                "اولین Sync",
                f"🎉 اولین Sync موفق!\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )
        elif result.total_new == 0:
            QMessageBox.information(
                self,
                "بدون تغییر",
                f"✨ هیچ تغییر جدیدی نیست\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )
        else:
            QMessageBox.information(
                self,
                "تغییرات جدید",
                f"📢 تغییرات جدید:\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n\n"
                f"⏱️ {result.duration_seconds:.1f} ثانیه",
            )

    def _on_sync_error(self, message: str) -> None:
        self.progress.setVisible(False)
        self.update_btn.setEnabled(True)
        QMessageBox.critical(self, "خطا در Sync", message)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None