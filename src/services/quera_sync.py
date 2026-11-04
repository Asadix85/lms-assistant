"""Sync Service برای Quera — نسخه اصلاح‌شده."""

import time

from loguru import logger

from src.core.quera_auth import QueraAuth
from src.core.quera_client import QueraHttpClient
from src.parsers.quera import QueraParser
from src.storage.repositories import QueraAssignmentRepository
from src.storage.repositories.quera_repo import QueraCourseRepository


class QueraSyncService:
    """Sync تمرین‌های Quera با دیتابیس."""

    def __init__(
        self,
        username: str,
        password: str,
        db,
        user_id: str,
    ) -> None:
        if not user_id:
            raise ValueError("QueraSyncService نیازمند user_id است")
        self.username = username
        self.password = password
        self.db = db
        self.user_id = user_id

        self.client = QueraHttpClient()
        self.auth = QueraAuth(self.client)
        self.parser = QueraParser()
        self.repo = QueraAssignmentRepository(db, user_id)
        self.course_repo = QueraCourseRepository(db, user_id)

    def sync(self) -> dict:
        """اجرای Sync کامل."""
        start = time.perf_counter()
        result = {
            "new": 0,
            "updated": 0,
            "total": 0,
            "courses": 0,
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

            # === ۳. Parse assignments ===
            logger.info("🔍 پارس HTML (تمرین‌ها)...")
            assignments = self.parser.parse_course_page(r.text)

            # === ۴. Parse courses ===
            logger.info("🔍 پارس HTML (کلاس‌ها)...")
            courses = self.parser.parse_courses(r.text)

            # === ۵. ذخیره تمرین‌ها ===
            logger.info(f"💾 ذخیره {len(assignments)} تمرین...")
            for a in assignments:
                existing = self.repo.get_by_id(a.id)
                self.repo.save(a)
                if existing is None:
                    result["new"] += 1
                else:
                    result["updated"] += 1

            # === ۶. ذخیره کلاس‌ها ===
            logger.info(f"💾 ذخیره {len(courses)} کلاس...")
            for c in courses:
                c.assignments_count = sum(
                    1 for a in assignments if a.course_name == c.name
                )
                self.course_repo.save(c)

            result["total"] = len(assignments)
            result["courses"] = len(courses)

            logger.info(
                f"✅ Quera Sync: {result['new']} جدید, "
                f"{result['updated']} به‌روزرسانی, "
                f"{len(courses)} کلاس"
            )

        except Exception as e:
            logger.exception("خطا در Quera Sync")
            result["error"] = str(e)

        finally:
            self.client.close()
            result["duration"] = time.perf_counter() - start

        return result