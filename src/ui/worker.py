"""Worker برای Sync در thread جداگانه."""

from PySide6.QtCore import QObject, Signal

from src.services.lms_assistant import LMSAssistant
from src.services.notifier import Notifier
from src.services.sync_progress import SyncProgress
from src.services.sync_result import SyncResult
from src.services.sync_service import SyncService
from src.storage.database import Database
from src.storage.repositories import SettingRepository


class SyncWorker(QObject):
    """Worker که در thread جداگانه Sync می‌کند."""

    started = Signal()
    finished = Signal(SyncResult)
    error = Signal(str)
    progress = Signal(object)  # ← SyncProgress

    def __init__(
        self,
        username: str,
        password: str,
        db_path: str,
        notify: bool = True,
    ) -> None:
        super().__init__()
        self.username = username
        self.password = password
        self.db_path = db_path
        self.notify = notify

    def run(self) -> None:
        try:
            self.started.emit()

            with Database(self.db_path) as db:
                db.init_schema()

                # progress اولیه
                self._emit_progress(
                    phase="login",
                    message="ورود به LMS...",
                    current=0,
                    total=1,
                )

                with LMSAssistant(
                    self.username, self.password
                ) as assistant:
                    if not assistant.login():
                        self.error.emit("ورود به LMS ناموفق بود")
                        return

                    # ذخیره‌ی نام کاربر
                    if assistant.full_name:
                        SettingRepository(db).set(
                            "full_name", assistant.full_name
                        )

                    # progress
                    self._emit_progress(
                        phase="login",
                        message="ورود موفق",
                        current=1,
                        total=1,
                    )

                    # Sync با callback
                    sync = SyncService(assistant, db)
                    result = sync.sync(on_progress=self._on_sync_progress)

            if self.notify and not result.has_error:
                notifier = Notifier()
                notifier.notify_sync_result(result)

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")

    def _on_sync_progress(self, progress: SyncProgress) -> None:
        """Callback از SyncService."""
        self.progress.emit(progress)

    def _emit_progress(
        self,
        phase: str,
        message: str,
        current: int = 0,
        total: int = 0,
        changes: dict | None = None,
    ) -> None:
        """کمکی برای emit progress اولیه."""
        progress = SyncProgress(
            phase=phase,
            phase_index=0,
            total_phases=6,
            current=current,
            total=total,
            message=message,
            changes=changes or {},
            elapsed=0.0,
        )
        self.progress.emit(progress)