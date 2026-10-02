"""Worker برای Sync در thread جداگانه (UI freeze نشود)."""

from PySide6.QtCore import QObject, QThread, Signal

from src.services.lms_assistant import LMSAssistant
from src.services.sync_service import SyncService
from src.services.sync_result import SyncResult
from src.storage.database import Database


class SyncWorker(QObject):
    """Worker که در thread جداگانه Sync می‌کند."""

    # Signals
    started = Signal()
    finished = Signal(SyncResult)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, username: str, password: str, db_path: str) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.db_path = db_path

    def run(self) -> None:
        """اجرای Sync (در thread جداگانه)."""
        try:
            self.started.emit()
            self.progress.emit("اتصال به دیتابیس...")

            with Database(self.db_path) as db:
                db.init_schema()

                self.progress.emit("ورود به LMS...")
                with LMSAssistant(self.username, self.password) as assistant:
                    if not assistant.login():
                        self.error.emit("ورود به LMS ناموفق بود")
                        return

                    self.progress.emit("هماهنگ‌سازی...")
                    sync = SyncService(assistant, db)
                    result = sync.sync()

                self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")