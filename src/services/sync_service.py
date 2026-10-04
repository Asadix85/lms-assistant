"""Sync Service: هماهنگ‌سازی LMS و Database."""

import time
from datetime import datetime

from loguru import logger

from src.collectors.members import MembersCollector
from src.models.change import Change, ChangeType, EntityType
from src.models.member import Member, MemberType
from src.parsers.members import MemberParser
from src.services.lms_assistant import LMSAssistant
from src.services.settings_manager import SettingsManager
from src.services.sync_result import SyncResult
from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
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
        self.post_repo = PostRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.member_repo = MemberRepository(db)
        self.setting_repo = SettingRepository(db)
        self.change_repo = ChangeRepository(db)

    def sync(self) -> SyncResult:
        start = time.time()
        result = SyncResult()

        try:
            first_sync = self.setting_repo.get(self.FIRST_SYNC_KEY) != "true"
            result.is_first_sync = first_sync
            logger.info(f"شروع Sync (اولین بار: {first_sync})")

            # ⚠️ خواندن تنظیمات Sync
            sync_settings = SettingsManager.get_sync_settings()
            logger.info(f"تنظیمات Sync: {sync_settings}")

            # === دروس (همیشه) ===
            self._sync_courses(result, first_sync)

            # === اختیاری ===
            if sync_settings["contents"]:
                self._sync_contents(result, first_sync)

            if sync_settings["events"]:
                self._sync_events(result, first_sync)

            if sync_settings["posts"] or sync_settings["assignments"]:
                self._sync_wall(
                    result,
                    first_sync,
                    sync_posts=sync_settings["posts"],
                    sync_assignments=sync_settings["assignments"],
                )

            if sync_settings["members"]:
                self._sync_members(result, first_sync)

            # === ذخیره ===
            if result.changes and not first_sync:
                self.change_repo.save_many(result.changes)

            if first_sync:
                self.setting_repo.set(self.FIRST_SYNC_KEY, "true")
                logger.info("✅ اولین Sync تمام شد")

            self.setting_repo.set(self.LAST_SYNC_KEY, datetime.now().isoformat())

            result.duration_seconds = time.time() - start
            logger.info(f"✅ Sync تمام شد در {result.duration_seconds:.1f} ثانیه")

        except Exception as e:
            logger.exception(f"❌ خطا در Sync: {e}")
            result.error = str(e)

        return result

    # === Courses ===

    def _sync_courses(self, result: SyncResult, first_sync: bool) -> None:
        logger.debug("Sync دروس...")

        lms_courses = self.assistant.get_all_courses()
        lms_ids = {c.id for c in lms_courses}
        db_ids = {c.id for c in self.course_repo.get_all()}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for c in lms_courses:
            if c.id in new_ids:
                self.course_repo.save(c)
                result.courses_new += 1
                result.changes.append(Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.COURSE,
                    entity_id=c.id,
                    data={"name": c.name, "domain": c.domain},
                ))
                if not first_sync:
                    logger.info(f"🆕 درس جدید: {c.name}")
            elif c.id in common_ids:
                self.course_repo.save(c)
                result.courses_updated += 1

        for cid in removed_ids:
            result.courses_removed += 1
            result.changes.append(Change(
                type=ChangeType.REMOVED,
                entity_type=EntityType.COURSE,
                entity_id=cid,
            ))

        if first_sync:
            self.course_repo.mark_all_seen()

    # === Contents ===

    def _sync_contents(self, result: SyncResult, first_sync: bool) -> None:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.debug("Sync محتوا (موازی)...")

        courses = self.assistant.get_active_courses()

        def fetch_course_contents(course):
            try:
                contents = self.assistant.get_course_contents(course)
                return course.name, contents, None
            except Exception as e:
                return course.name, [], str(e)

        all_lms = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_course_contents, c): c
                for c in courses
            }

            for future in as_completed(futures):
                course_name, contents, error = future.result()
                if error:
                    logger.error(f"خطا در محتوای {course_name}: {error}")
                else:
                    all_lms.extend(contents)

        lms_ids = {c.id for c in all_lms}
        db_ids = {c.id for c in self.content_repo.get_all()}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for c in all_lms:
            if c.id in new_ids:
                self.content_repo.save(c)
                result.contents_new += 1
                result.changes.append(Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.CONTENT,
                    entity_id=c.id,
                    course_id=c.course_id,
                    data={"title": c.title, "type": c.content_type},
                ))
                if not first_sync:
                    logger.info(f"🆕 فایل جدید: {c.title}")
            elif c.id in common_ids:
                self.content_repo.save(c)
                result.contents_updated += 1

        for cid in removed_ids:
            result.contents_removed += 1

        if first_sync:
            self.content_repo.mark_all_seen()

    # === Events ===

    def _sync_events(self, result: SyncResult, first_sync: bool) -> None:
        logger.debug("Sync رویدادها...")

        lms_events = self.assistant.get_all_events()
        lms_ids = {e.id for e in lms_events}
        db_ids = {e.id for e in self.event_repo.get_all()}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for e in lms_events:
            if e.id in new_ids:
                self.event_repo.save(e)
                result.events_new += 1
                result.changes.append(Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.EVENT,
                    entity_id=e.id,
                    course_id=e.course_id,
                    data={"title": e.title},
                ))
                if not first_sync:
                    logger.info(f"🆕 رویداد جدید: {e.title}")
            elif e.id in common_ids:
                self.event_repo.save(e)
                result.events_updated += 1

        for eid in removed_ids:
            result.events_removed += 1
            result.changes.append(Change(
                type=ChangeType.REMOVED,
                entity_type=EntityType.EVENT,
                entity_id=eid,
            ))

        if first_sync:
            self.event_repo.mark_all_seen()

    # === Wall (Posts + Assignments) ===

    def _sync_wall(
            self,
            result: SyncResult,
            first_sync: bool,
            sync_posts: bool = True,
            sync_assignments: bool = True,
    ) -> None:
        """Sync wall (موازی)."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.debug(f"Sync wall (posts={sync_posts}, assignments={sync_assignments})")

        courses = self.assistant.get_active_courses()

        def fetch_course_wall(course):
            try:
                posts, assignments = self.assistant.get_course_wall(course)
                return course.name, posts, assignments, None
            except Exception as e:
                return course.name, [], [], str(e)

        all_posts = []
        all_assignments = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_course_wall, c): c
                for c in courses
            }

            for future in as_completed(futures):
                course_name, posts, assignments, error = future.result()
                if error:
                    logger.error(f"خطا در wall {course_name}: {error}")
                else:
                    if sync_posts:
                        all_posts.extend(posts)
                    if sync_assignments:
                        all_assignments.extend(assignments)

        if sync_posts:
            self._sync_posts(result, all_posts, first_sync)
        if sync_assignments:
            self._sync_assignments(result, all_assignments, first_sync)

    def _sync_posts(self, result: SyncResult, all_posts: list, first_sync: bool) -> None:
        """Sync پست‌ها."""
        lms_post_ids = {p.id for p in all_posts}
        db_post_ids = {p.id for p in self.post_repo.get_all()}

        new_post_ids = lms_post_ids - db_post_ids
        removed_post_ids = db_post_ids - lms_post_ids
        common_post_ids = lms_post_ids & db_post_ids

        for p in all_posts:
            if p.id in new_post_ids:
                self.post_repo.save(p)
                result.posts_new += 1
                result.changes.append(Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.COURSE,
                    entity_id=p.id,
                    course_id=p.course_id,
                    data={"author": p.author, "text": p.text[:100]},
                ))
                if not first_sync:
                    logger.info(f"🆕 پست جدید از {p.author}: {p.text[:40]}")
            elif p.id in common_post_ids:
                self.post_repo.save(p)
                result.posts_updated += 1

        for pid in removed_post_ids:
            result.posts_removed += 1

        if first_sync:
            self.post_repo.mark_all_seen()

    def _sync_assignments(self, result: SyncResult, all_assignments: list, first_sync: bool) -> None:
        """Sync تکالیف."""
        lms_ids = {a.id for a in all_assignments}
        db_ids = {a.id for a in self.assignment_repo.get_all()}

        new_ids = lms_ids - db_ids
        removed_ids = db_ids - lms_ids
        common_ids = lms_ids & db_ids

        for a in all_assignments:
            if a.id in new_ids:
                self.assignment_repo.save(a)
                result.assignments_new += 1
                result.changes.append(Change(
                    type=ChangeType.NEW,
                    entity_type=EntityType.COURSE,
                    entity_id=a.id,
                    course_id=a.course_id,
                    data={
                        "title": a.title,
                        "deadline": a.deadline.isoformat() if a.deadline else None,
                    },
                ))
                if not first_sync:
                    logger.info(f"🆕 تکلیف جدید: {a.title[:50]}")
            elif a.id in common_ids:
                self.assignment_repo.save(a)
                result.assignments_updated += 1

        for aid in removed_ids:
            result.assignments_removed += 1

        if first_sync:
            self.assignment_repo.mark_all_seen()

    # === Members (اختیاری - کند) ===

    def _sync_members(self, result: SyncResult, first_sync: bool) -> None:
        """Sync همکلاسی‌ها (موازی)."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from src.collectors.members import MembersCollector
        from src.parsers.members import MemberParser

        logger.debug("Sync اعضا (موازی)...")

        courses = self.assistant.get_active_courses()
        total_members = 0

        def fetch_course_members(course):
            try:
                collector = MembersCollector(self.assistant.client, course)
                parser = MemberParser(
                    course_id=course.group_id,
                    teacher_name=course.teacher,
                )
                members = []

                # دانشجویان
                for html in collector.collect_all_students():
                    members.extend(parser.parse(html, is_admin_page=False))

                # استادان
                admin_html = collector.collect_admins(page=1)
                members.extend(parser.parse(admin_html, is_admin_page=True))

                return course.name, members, None
            except Exception as e:
                return course.name, [], str(e)

        # ⚠️ موازی‌سازی با ۵ worker
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_course_members, c): c
                for c in courses
            }

            for future in as_completed(futures):
                course_name, members, error = future.result()
                if error:
                    logger.error(f"خطا در اعضای {course_name}: {error}")
                else:
                    for m in members:
                        self.member_repo.save(m)
                    total_members += len(members)
                    logger.debug(f"  ✅ {course_name}: {len(members)} عضو")

        logger.info(f"✅ {total_members} عضو Sync شد (موازی)")