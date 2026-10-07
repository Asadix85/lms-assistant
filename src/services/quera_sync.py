"""Sync Service برای Quera."""

import time

from loguru import logger

from src.core.quera_auth import QueraAuth
from src.core.quera_client import QueraHttpClient
from src.parsers.quera import QueraParser
from src.storage.repositories import QueraAssignmentRepository


class QueraSyncService:
    """Sync تمرین‌های Quera با دیتابیس."""

    def __init__(
        self,
        username: str,
        password: str,
        db,
    ) -> None:
        self.username = username
        self.password = password
        self.db = db

        self.client = QueraHttpClient()
        self.auth = QueraAuth(self.client)
        self.parser = QueraParser()
        self.repo = QueraAssignmentRepository(db)

    def sync(self) -> dict:
        """اجرای Sync کامل.

        Returns:
            dict با آمار: {"new": int, "updated": int, "total": int, "error": str|None}
        """
        start = time.perf_counter()
        result = {
            "new": 0,
            "updated": 0,
            "total": 0,
            "error": None,
            "duration": 0.0,
        }

        try:
            # === ۱. Login ===
            logger.info("🔐 Login به Quera...")
            if not self.auth.login(self.username, self.password):
                result["error"] = "Login ناموفق"
                return result

            logger.info("✅ Login موفق")

            # === ۲. دریافت /course ===
            logger.info("📥 دریافت /course...")
            r = self.client.get("/course")

            if r.status_code != 200:
                result["error"] = f"HTTP {r.status_code}"
                return result

            # === ۳. Parse ===
            logger.info("🔍 پارس HTML...")
            assignments = self.parser.parse_course_page(r.text)

            # === ۴. ذخیره در دیتابیس ===
            logger.info(f"💾 ذخیره {len(assignments)} تمرین...")
            for a in assignments:
                existing = self.repo.get_by_id(a.id)
                self.repo.save(a)

                if existing is None:
                    result["new"] += 1
                else:
                    result["updated"] += 1

            result["total"] = len(assignments)
            logger.info(
                f"✅ Quera Sync: {result['new']} جدید, "
                f"{result['updated']} به‌روزرسانی"
            )

        except Exception as e:
            logger.exception("خطا در Quera Sync")
            result["error"] = str(e)

        finally:
            self.client.close()
            result["duration"] = time.perf_counter() - start

        return result