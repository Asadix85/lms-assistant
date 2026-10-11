"""Push دیتابیس به GitHub بعد از Sync.

این سرویس با subprocess کار می‌کنه و:
1. data/lms.db رو stage می‌کنه
2. اگه تغییری هست، commit می‌کنه
3. به شاخه‌ی فعلی push می‌کنه
"""

import subprocess
from pathlib import Path

from loguru import logger


class GitPusher:
    """مدیریت push دیتابیس به GitHub."""

    DB_PATH = "data/lms.db"

    def __init__(self, repo_root: str = ".") -> None:
        self.repo_root = Path(repo_root).resolve()

    def _run_git(
        self,
        *args: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """اجرای دستور Git."""
        try:
            return subprocess.run(
                ["git", *args],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=check,
                timeout=60,
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"Git timeout: {' '.join(args)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Git failed: git {' '.join(args)}\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}"
            )
            raise

    def push_db(self) -> bool:
        """Push دیتابیس به GitHub (شاخه‌ی فعلی)."""
        db = self.repo_root / self.DB_PATH
        if not db.exists():
            logger.warning(f"دیتابیس پیدا نشد: {db}")
            return False

        try:
            # === ۱. Stage دیتابیس ===
            self._run_git("add", "data/lms.db")
            logger.debug("✅ داده stage شد")

            # === ۲. چک کن تغییری هست؟ ===
            # (status --porcelain خالی باشه → تغییری نیست)
            status = self._run_git(
                "status", "--porcelain", "data/lms.db", check=False
            )
            if not status.stdout.strip():
                logger.info("ℹ️ دیتابیس تغییری نکرده — نیازی به push نیست")
                return False

            # === ۳. Commit ===
            from datetime import datetime
            commit_msg = (
                f"data: auto-sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            self._run_git("commit", "-m", commit_msg)
            logger.debug(f"✅ commit: {commit_msg}")

            # === ۴. Push ===
            # شاخه‌ی فعلی رو پیدا کن
            branch_result = self._run_git(
                "branch", "--show-current", check=False
            )
            branch = branch_result.stdout.strip() or "master"

            self._run_git("push", "origin", branch)
            logger.info(f"✅ DB به GitHub push شد (شاخه: {branch})")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"خطا در Git push: {e}")
            return False
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره: {e}")
            return False