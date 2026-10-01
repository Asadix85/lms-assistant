"""Sync Service: هماهنگ‌سازی LMS و Database."""

import time

from loguru import logger

from src.core.exceptions import LMSError
from src.models.change import Change, ChangeType, EntityType
from src.services.lms_assistant import LMSAssistant
from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)


class SyncService:
    """هماهنگ‌سازی کامل LMS با Database."""

    FIRST_SYNC_KEY = "first_sync_done"
    LAST_SYNC_KEY = "last_sync_at"

    def __init__(self, assistant: LMSAssistant, db: Database) -> None:
        self.assistant = assistant
        self.db = db

        self.course_repo = CourseRepository(db)
        self.content_repo = ContentRepository(db)
        self.event_repo = EventRepository(db)
        self.setting_repo = SettingRepository(db)

    # === Main Sync ===

    def sync(self) -> SyncResult:
        """هماهنگ‌سازی کامل."""
        start = time.time()
        result = SyncResult()

        try:
            # ۱. آیا اولین Sync است؟
            first_sync = self.setting_repo.get(self.FIRST_SYNC_KEY) != "true"
            result.is_first_sync = first_sync
            logger.info(f"شروع Sync (اولین بار: {first_sync})")

            # ۲. Sync دروس
            self._sync_courses(result, first_sync)

            # ۳. Sync محتوا
            self._sync_contents(result, first_sync)

            # ۴. Sync رویدادها
            self._sync_events(result, first_sync)

            # ۵. علامت‌گذاری
            if first_sync:
                self.setting_repo.set(self.FIRST_SYNC_KEY, "true")
                logger.info("✅ اولین Sync تمام شد")

            # ۶. ذخیره زمان
            from datetime import datetime
            self.setting_repo.set(self.LAST_SYNC_KEY, datetime.now().isoformat())

            result.duration_seconds = time.time() - start
            logger.info(f"✅ Sync تمام شد در {result.duration_seconds:.1f} ثانیه")

        except Exception as e:
            logger.exception(f"❌ خطا در Sync: {e}")
            result.error = str(e)

        return result

    # === Courses ===

    def _sync_courses(self, result: SyncResult, first_sync: bool) -> None:
        """Sync دروس."""
        logger.debug("Sync دروس...")

        # LMS
        lms_courses = self.assistant.get_all_courses()
        lms_ids = {c.id for c in lms_courses}

        # DB
        db_courses = self.course_repo.get_all()
        db_ids = {c.id for c in db_courses}

        # محاسبه
        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        # درج جدیدها
        for c in lms_courses:
            if c.id in new_ids:
                self.course_repo.save(c)
                result.courses_new += 1

                change = Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.COURSE,
                    entity_id=c.id,
                    data={"name": c.name, "domain": c.domain},
                )
                result.changes.append(change)

                if not first_sync:
                    logger.info(f"🆕 درس جدید: {c.name}")

            elif c.id in common_ids:
                self.course_repo.save(c)  # به‌روزرسانی
                result.courses_updated += 1

        # حذف‌شده‌ها
        for cid in removed_ids:
            result.courses_removed += 1
            change = Change(
                type=ChangeType.REMOVED,
                entity_type=EntityType.COURSE,
                entity_id=cid,
            )
            result.changes.append(change)

        # اگر اولین Sync، is_new = 0
        if first_sync:
            self.course_repo.mark_all_seen()

    # === Contents ===

    def _sync_contents(self, result: SyncResult, first_sync: bool) -> None:
        """Sync محتوا."""
        logger.debug("Sync محتوا...")

        # همه محتوای LMS
        lms_contents_by_course = self.assistant.get_all_contents()
        all_lms_contents = []
        for contents in lms_contents_by_course.values():
            all_lms_contents.extend(contents)

        lms_ids = {c.id for c in all_lms_contents}
        db_contents = self.content_repo.get_all()
        db_ids = {c.id for c in db_contents}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for c in all_lms_contents:
            if c.id in new_ids:
                self.content_repo.save(c)
                result.contents_new += 1

                change = Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.CONTENT,
                    entity_id=c.id,
                    course_id=c.course_id,
                    data={"title": c.title, "type": c.content_type},
                )
                result.changes.append(change)

                if not first_sync:
                    logger.info(f"🆕 فایل جدید: {c.title}")

            elif c.id in common_ids:
                self.content_repo.save(c)
                result.contents_updated += 1

        for cid in removed_ids:
            result.contents_removed += 1
            change = Change(
                type=ChangeType.REMOVED,
                entity_type=EntityType.CONTENT,
                entity_id=cid,
            )
            result.changes.append(change)

        if first_sync:
            self.content_repo.mark_all_seen()

    # === Events ===

    def _sync_events(self, result: SyncResult, first_sync: bool) -> None:
        """Sync رویدادها."""
        logger.debug("Sync رویدادها...")

        lms_events = self.assistant.get_all_events()
        lms_ids = {e.id for e in lms_events}
        db_events = self.event_repo.get_all()
        db_ids = {e.id for e in db_events}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for e in lms_events:
            if e.id in new_ids:
                self.event_repo.save(e)
                result.events_new += 1

                change = Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.EVENT,
                    entity_id=e.id,
                    course_id=e.course_id,
                    data={"title": e.title},
                )
                result.changes.append(change)

                if not first_sync:
                    logger.info(f"🆕 رویداد جدید: {e.title}")

            elif e.id in common_ids:
                self.event_repo.save(e)
                result.events_updated += 1

        for eid in removed_ids:
            result.events_removed += 1
            change = Change(
                type=ChangeType.REMOVED,
                entity_type=EntityType.EVENT,
                entity_id=eid,
            )
            result.changes.append(change)

        if first_sync:
            self.event_repo.mark_all_seen()