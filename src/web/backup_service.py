"""بکاپ زمان‌بندی‌شده SQLite و نگهداری تعداد محدود."""

from __future__ import annotations

import shutil
import threading
from datetime import datetime
from pathlib import Path

from loguru import logger

from config.settings import settings

DEFAULT_INTERVAL_HOURS = 24
DEFAULT_KEEP = 14


def backup_dir() -> Path:
    return Path(settings.db_path).parent / "backups"


def create_backup(*, keep: int = DEFAULT_KEEP) -> Path | None:
    db_path = Path(settings.db_path)
    if not db_path.exists():
        logger.warning("بکاپ: فایل DB نیست {}", db_path)
        return None
    bdir = backup_dir()
    bdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = bdir / f"lms_auto_{stamp}.db"
    shutil.copy2(db_path, dest)
    logger.info("بکاپ خودکار ساخته شد: {}", dest)
    _prune(bdir, keep=keep)
    return dest


def _prune(bdir: Path, keep: int) -> None:
    files = sorted(bdir.glob("lms_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        try:
            old.unlink()
            logger.debug("بکاپ قدیمی حذف شد: {}", old.name)
        except OSError:
            pass


def restore_instructions() -> str:
    return (
        "بازیابی بکاپ:\n"
        "1) سرور را متوقف کنید.\n"
        "2) از فایل فعلی DB کپی بگیرید.\n"
        f"3) یکی از فایل‌های {backup_dir()}/lms_*.db را روی مسیر DB کپی کنید:\n"
        f"   {settings.db_path}\n"
        "4) سرور را دوباره اجرا کنید.\n"
    )


class BackupScheduler:
    def __init__(self, interval_hours: float = DEFAULT_INTERVAL_HOURS, keep: int = DEFAULT_KEEP) -> None:
        self.interval = max(1.0, interval_hours) * 3600
        self.keep = keep
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="db-backup")
        self._thread.start()
        logger.info("زمان‌بند بکاپ فعال شد (هر {} ساعت، نگهداشت {})", self.interval / 3600, self.keep)

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        # یک بکاپ سریع در استارت
        try:
            create_backup(keep=self.keep)
        except Exception as e:
            logger.error("بکاپ اولیه ناموفق: {}", e)
        while not self._stop.wait(self.interval):
            try:
                create_backup(keep=self.keep)
            except Exception as e:
                logger.error("بکاپ دوره‌ای ناموفق: {}", e)
