"""Session Manager: مدیریت لاگین LMS/Quera و Sync در بک‌گراند (جایگزین Worker کیوتی)."""

import asyncio
import threading
import time
from collections.abc import Callable

from loguru import logger

from src.services.credential_provider import CredentialProvider, Credentials
from src.services.lms_assistant import LMSAssistant
from src.services.quera_sync import QueraSyncService
from src.services.sync_progress import SyncProgress
from src.services.sync_result import SyncResult
from src.services.sync_service import SyncService
from src.storage.database import Database


class SessionManager:
    """مدیریت session وب: credentials، اتصال LMS، و اجرای sync در thread."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._lock = threading.Lock()
        self._assistant: LMSAssistant | None = None
        self._creds: Credentials | None = None

        # === Sync state ===
        self._sync_thread: threading.Thread | None = None
        self._sync_running = False
        self._latest_progress: SyncProgress | None = None
        self._last_result: SyncResult | None = None
        self._subscribers: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    # =========================================================
    # Credentials / Login
    # =========================================================

    @property
    def creds(self) -> Credentials:
        if self._creds is None:
            self._creds = CredentialProvider.load()
        return self._creds

    def set_credentials(
        self,
        lms_username: str,
        lms_password: str,
        quera_username: str = "",
        quera_password: str = "",
    ) -> None:
        self._creds = Credentials(
            lms_username=lms_username,
            lms_password=lms_password,
            quera_username=quera_username,
            quera_password=quera_password,
        )
        CredentialProvider.update(lms_username, lms_password, quera_username, quera_password)
        # اگر session قبلی وجود داشت، باطل شود
        with self._lock:
            if self._assistant:
                try:
                    self._assistant.close()
                except Exception:
                    pass
                self._assistant = None

    def get_assistant(self) -> LMSAssistant:
        """دریافت assistant لاگین‌شده (lazy login با لاک)."""
        with self._lock:
            if self._assistant and self._assistant.is_authenticated:
                return self._assistant

            creds = self.creds
            if not creds.lms_username or not creds.lms_password:
                raise PermissionError("اعتبارنامه LMS تنظیم نشده است")

            assistant = LMSAssistant(creds.lms_username, creds.lms_password)
            if not assistant.login():
                raise PermissionError("Login به LMS ناموفق بود")

            self._assistant = assistant
            return assistant

    @property
    def lms_logged_in(self) -> bool:
        a = self._assistant
        return bool(a and a.is_authenticated)

    @property
    def full_name(self) -> str | None:
        a = self._assistant
        return a.full_name if a else None

    def logout(self) -> None:
        with self._lock:
            if self._assistant:
                try:
                    self._assistant.close()
                except Exception:
                    pass
                self._assistant = None
        if self._creds:
            self.set_credentials("", "", self._creds.quera_username, self._creds.quera_password)

    # =========================================================
    # Sync (background thread + pub/sub برای SSE)
    # =========================================================

    @property
    def sync_running(self) -> bool:
        return self._sync_running

    @property
    def latest_progress(self) -> SyncProgress | None:
        return self._latest_progress

    @property
    def last_result(self) -> SyncResult | None:
        return self._last_result

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """اتصال event loop فست‌API برای publish رویدادهای sync."""
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)

    def _publish(self, event: dict) -> None:
        loop = self._loop
        if loop is None:
            return
        for q in list(self._subscribers):
            try:
                loop.call_soon_threadsafe(q.put_nowait, event)
            except RuntimeError:
                pass  # loop بسته شده

    def start_lms_sync(self) -> bool:
        """شروع sync LMS در thread جدا. اگر در حال اجرا باشد False برمی‌گرداند."""
        if self._sync_running:
            return False
        self._sync_running = True
        self._latest_progress = None
        self._last_result = None

        def on_progress(p: SyncProgress) -> None:
            self._latest_progress = p
            self._publish({"type": "progress", "data": p.to_dict() if hasattr(p, "to_dict") else {
                "phase": p.phase,
                "phase_index": p.phase_index,
                "total_phases": p.total_phases,
                "current": p.current,
                "total": p.total,
                "message": p.message,
                "percent": p.percent,
                "elapsed": round(p.elapsed, 1),
                "changes": p.changes,
            }})

        def run() -> None:
            try:
                assistant = self.get_assistant()
                service = SyncService(assistant, self.db)
                result = service.sync(on_progress=on_progress)
                self._last_result = result
                self._publish({
                    "type": "result",
                    "data": {
                        "ok": not result.has_error,
                        "error": result.error,
                        "summary": result.summary(),
                    },
                })
            except Exception as e:
                logger.exception("خطا در sync پس‌زمینه")
                self._publish({"type": "error", "data": {"message": str(e)}})
            finally:
                self._sync_running = False

        self._sync_thread = threading.Thread(target=run, daemon=True, name="lms-sync")
        self._sync_thread.start()
        return True

    def run_quera_sync(self) -> dict:
        """Sync Quera (سریع؛ همگام اجرا می‌شود داخل thread درخواست)."""
        creds = self.creds
        if not creds.quera_username or not creds.quera_password:
            return {"error": "اعتبارنامه Quera تنظیم نشده"}
        service = QueraSyncService(creds.quera_username, creds.quera_password, self.db)
        return service.sync()
