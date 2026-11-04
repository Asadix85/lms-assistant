"""Session Manager: مدیریت per-user برای LMS/Quera و Sync در بک‌گراند."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable

from loguru import logger

from src.services.lms_assistant import LMSAssistant
from src.services.quera_sync import QueraSyncService
from src.services.sync_progress import SyncProgress
from src.services.sync_result import SyncResult
from src.services.sync_service import SyncService
from src.storage.database import Database
from src.storage.repositories.user_repo import UserRepository


class SessionManager:
    """مدیریت session وب چندکاربره: assistantها per-user و sync در thread."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self._lock = threading.Lock()
        # user_id -> LMSAssistant
        self._assistants: dict[str, LMSAssistant] = {}
        # user_id فعال برای sync تک‌نخی فعلی (فاز ۱: یک sync سراسری)
        self._active_user_id: str | None = None

        self._sync_thread: threading.Thread | None = None
        self._sync_running = False
        self._latest_progress: SyncProgress | None = None
        self._last_result: SyncResult | None = None
        self._subscribers: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    # =========================================================
    # Per-user LMS assistant
    # =========================================================

    def set_active_user(self, user_id: str | None) -> None:
        self._active_user_id = user_id

    @property
    def active_user_id(self) -> str | None:
        return self._active_user_id

    def bind_assistant(self, user_id: str, assistant: LMSAssistant) -> None:
        with self._lock:
            old = self._assistants.get(user_id)
            if old is not None and old is not assistant:
                try:
                    old.close()
                except Exception:
                    pass
            self._assistants[user_id] = assistant
            self._active_user_id = user_id

    def drop_assistant(self, user_id: str) -> None:
        with self._lock:
            old = self._assistants.pop(user_id, None)
            if old is not None:
                try:
                    old.close()
                except Exception:
                    pass
            if self._active_user_id == user_id:
                self._active_user_id = None

    def get_assistant(self, user_id: str | None = None) -> LMSAssistant:
        """assistant لاگین‌شده برای user؛ در صورت نیاز از secrets دوباره می‌سازد."""
        uid = user_id or self._active_user_id
        if not uid:
            raise PermissionError("کاربر مشخص نیست")

        with self._lock:
            existing = self._assistants.get(uid)
            if existing and existing.is_authenticated:
                return existing

        repo = UserRepository(self.db)
        user = repo.get_by_id(uid)
        if not user:
            raise PermissionError("کاربر یافت نشد")
        secrets = repo.load_secrets(uid)
        if not secrets.get("lms_password"):
            raise PermissionError("اعتبارنامه LMS تنظیم نشده است — دوباره وارد شوید")

        assistant = LMSAssistant(user["lms_username"], secrets["lms_password"])
        if not assistant.login():
            raise PermissionError("Login به LMS ناموفق بود")

        self.bind_assistant(uid, assistant)
        return assistant

    def is_lms_live(self, user_id: str) -> bool:
        with self._lock:
            a = self._assistants.get(user_id)
            return bool(a and a.is_authenticated)

    def full_name_for(self, user_id: str) -> str | None:
        with self._lock:
            a = self._assistants.get(user_id)
            if a and a.full_name:
                return a.full_name
        user = UserRepository(self.db).get_by_id(user_id)
        return user.get("full_name") if user else None

    # سازگاری با کد قدیمی که بدون user_id صداید
    @property
    def lms_logged_in(self) -> bool:
        uid = self._active_user_id
        return self.is_lms_live(uid) if uid else False

    @property
    def full_name(self) -> str | None:
        uid = self._active_user_id
        return self.full_name_for(uid) if uid else None

    def logout_user(self, user_id: str) -> None:
        self.drop_assistant(user_id)

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
                pass

    def start_lms_sync(self, user_id: str | None = None) -> bool:
        if self._sync_running:
            return False

        uid = user_id or self._active_user_id
        if not uid:
            raise PermissionError("برای sync باید وارد شده باشید")

        self._active_user_id = uid
        self._sync_running = True
        self._latest_progress = None
        self._last_result = None

        def on_progress(p: SyncProgress) -> None:
            self._latest_progress = p
            self._publish(
                {
                    "type": "progress",
                    "data": p.to_dict()
                    if hasattr(p, "to_dict")
                    else {
                        "phase": p.phase,
                        "phase_index": p.phase_index,
                        "total_phases": p.total_phases,
                        "current": p.current,
                        "total": p.total,
                        "message": p.message,
                        "percent": p.percent,
                        "elapsed": round(p.elapsed, 1),
                        "changes": p.changes,
                    },
                }
            )

        def run() -> None:
            try:
                assistant = self.get_assistant(uid)
                service = SyncService(assistant, self.db, uid)
                result = service.sync(on_progress=on_progress)
                self._last_result = result

                if result.has_error:
                    self._publish(
                        {
                            "type": "result",
                            "data": {
                                "ok": False,
                                "error": result.error,
                                "summary": "سینک LMS ناموفق بود. سینک کوئرا انجام نشد.",
                            },
                        }
                    )
                    return

                self._publish(
                    {
                        "type": "progress",
                        "data": {
                            "phase": "quera",
                            "phase_index": 99,
                            "total_phases": 100,
                            "current": 0,
                            "total": 1,
                            "message": "در حال همگام‌سازی کوئرا...",
                            "percent": 99,
                            "elapsed": 0,
                            "changes": {},
                        },
                    }
                )

                quera_result = self.run_quera_sync(uid)

                if quera_result.get("error"):
                    self._publish(
                        {
                            "type": "result",
                            "data": {
                                "ok": True,
                                "error": None,
                                "summary": f"LMS: موفق | کوئرا: {quera_result['error']}",
                            },
                        }
                    )
                else:
                    self._publish(
                        {
                            "type": "result",
                            "data": {
                                "ok": True,
                                "error": None,
                                "summary": (
                                    f"LMS: {result.summary()} | کوئرا: "
                                    f"{quera_result.get('new', 0)} جدید، "
                                    f"{quera_result.get('updated', 0)} به‌روز"
                                ),
                            },
                        }
                    )
            except Exception as e:
                logger.exception("خطا در sync پس‌زمینه")
                self._publish({"type": "error", "data": {"message": str(e)}})
            finally:
                self._sync_running = False

        self._sync_thread = threading.Thread(target=run, daemon=True, name="full-sync")
        self._sync_thread.start()
        return True

    def run_quera_sync(self, user_id: str | None = None) -> dict:
        uid = user_id or self._active_user_id
        if not uid:
            return {"error": "کاربر مشخص نیست"}

        secrets = UserRepository(self.db).load_secrets(uid)
        if not secrets.get("quera_username") or not secrets.get("quera_password"):
            return {"error": "اعتبارنامه Quera تنظیم نشده"}

        service = QueraSyncService(
            secrets["quera_username"],
            secrets["quera_password"],
            self.db,
            uid,
        )
        return service.sync()
