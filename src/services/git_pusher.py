"""Push دیتابیس به GitHub بعد از Sync."""

import shutil
import subprocess
from pathlib import Path

from loguru import logger


class GitPusher:
    """مدیریت push دیتابیس به GitHub."""

    DATA_REPO = "data"  # شاخه‌ی مخصوص داده
    DB_PATH = "data/lms.db"

    def __init__(self, repo_root: str = ".") -> None:
        self.repo_root = Path(repo_root)

    def push_db(self) -> bool:
        """Push دیتابیس به شاخه‌ی data."""
        try:
            db = self.repo_root / self.DB_PATH
            if not db.exists():
                logger.warning("دیتابیس پیدا نشد")
                return False

            # کپی DB به یه پوشه‌ی temp
            temp_dir = self.repo_root / ".tmp_push"
            temp_dir.mkdir(exist_ok=True)

            # اگه پوشه‌ی .git/data وجود نداره، clone کن
            # (برای بار اول)
            # ...

            # commit و push
            subprocess.run(
                ["git", "add", "data/lms.db"],
                cwd=self.repo_root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"data: update lms.db"],
                cwd=self.repo_root,
                check=True,
            )
            subprocess.run(
                ["git", "push", "origin", "data"],
                cwd=self.repo_root,
                check=True,
            )

            logger.info("✅ دیتابیس به GitHub push شد")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"خطا در Git push: {e}")
            return False