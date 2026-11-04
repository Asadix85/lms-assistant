"""سرویس اصلی Sync بین LMS و دیتابیس."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from loguru import logger

from src.collectors.members import MembersCollector
from src.models.change import Change, ChangeType, EntityType
from src.parsers.members import MemberParser
from src.services.sync_progress import (
    PHASE_WEIGHTS,
    ProgressCallback,
    SyncProgress,
)
from src.services.sync_result import SyncResult
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
    """هماهنگ‌سازی اطلاعات LMS با دیتابیس محلی."""

    PHASE_ORDER = [
        "login",
        "courses",
        "contents",
        "events",
        "wall",
        "members",
    ]

    DOMAIN_URLS = {
        "lms3": "https://lms3.ui.ac.ir",
        "lms4": "https://lms4.ui.ac.ir",
        "lms5": "https://lms5.ui.ac.ir",
    }

    def __init__(self, assistant, db, user_id: str) -> None:
        if not user_id:
            raise ValueError("SyncService نیازمند user_id است")
        self.assistant = assistant
        self.db = db
        self.user_id = user_id

        self.course_repo = CourseRepository(db, user_id)
        self.content_repo = ContentRepository(db, user_id)
        self.event_repo = EventRepository(db, user_id)
        self.post_repo = PostRepository(db, user_id)
        self.assignment_repo = AssignmentRepository(db, user_id)
        self.member_repo = MemberRepository(db, user_id)
        self.change_repo = ChangeRepository(db, user_id)
        self.setting_repo = SettingRepository(db, user_id)

        self._on_progress: ProgressCallback = lambda p: None
        self._start_time: float = 0.0
        self._enabled_phases: list[str] = []

    # =============================================================
    # Progress helpers
    # =============================================================

    def _notify(
        self,
        phase: str,
        message: str = "",
        current: int = 0,
        total: int = 0,
        changes: dict[str, int] | None = None,
    ) -> None:
        """ارسال وضعیت progress به callback."""
        phase_index = 0
        if phase in self._enabled_phases:
            phase_index = self._enabled_phases.index(phase)

        progress = SyncProgress(
            phase=phase,
            phase_index=phase_index,
            total_phases=len(self._enabled_phases),
            current=current,
            total=total,
            message=message,
            changes=changes or {},
            elapsed=time.perf_counter() - self._start_time,
        )
        self._on_progress(progress)

    def _result_changes(self, result: SyncResult) -> dict[str, int]:
        """تغییرات زنده از SyncResult."""
        return {
            "courses": result.courses_new,
            "contents": result.contents_new,
            "events": result.events_new,
            "posts": result.posts_new,
            "assignments": result.assignments_new,
            "members": result.members_new,
        }

    # =============================================================
    # Main sync
    # =============================================================

    def sync(
        self,
        on_progress: ProgressCallback | None = None,
    ) -> SyncResult:
        """اجرای کامل Sync."""
        start_time = time.perf_counter()
        self._start_time = start_time

        if on_progress is not None:
            self._on_progress = on_progress

        result = SyncResult()

        try:
            # =====================================================
            # Settings
            # =====================================================

            first_sync = (
                self.setting_repo.get("first_sync", "pending") != "done"
            )
            result.is_first_sync = first_sync

            sync_contents = (
                self.setting_repo.get("sync_contents", "true") == "true"
            )
            sync_events = (
                self.setting_repo.get("sync_events", "true") == "true"
            )
            sync_wall = (
                self.setting_repo.get("sync_wall", "true") == "true"
            )
            sync_members = (
                self.setting_repo.get("sync_members", "false") == "true"
            )

            # === ساخت لیست فازهای فعال ===
            self._enabled_phases = ["login", "courses", "schedules"]
            if sync_contents:
                self._enabled_phases.append("contents")
            if sync_events:
                self._enabled_phases.append("events")
            if sync_wall:
                self._enabled_phases.append("wall")
            if sync_members:
                self._enabled_phases.append("members")

            # =====================================================
            # Login
            # =====================================================

            self._notify(
                phase="login",
                message="ورود به LMS...",
                current=1,
                total=1,
            )

            # =====================================================
            # Courses
            # =====================================================

            self._notify(
                phase="courses",
                message="دریافت لیست درس‌ها...",
                current=0,
                total=1,
            )

            phase_start = time.perf_counter()

            courses = self.assistant.get_all_courses()
            active_courses = [c for c in courses if c.is_active]

            self._sync_courses(result, first_sync, courses)

            self._notify(
                phase="courses",
                message="درس‌ها دریافت شد",
                current=1,
                total=1,
                changes=self._result_changes(result),
            )

            logger.info(
                "Sync phase 'courses' completed in {:.2f}s",
                time.perf_counter() - phase_start,
            )

            # =====================================================
            # Contents
            # =====================================================

            if sync_contents:
                phase_start = time.perf_counter()

                self._notify(
                    phase="contents",
                    message="دریافت محتوای درس‌ها...",
                    current=0,
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                self._sync_contents(result, first_sync, active_courses)

                self._notify(
                    phase="contents",
                    message="محتوای درس‌ها دریافت شد",
                    current=len(active_courses),
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                logger.info(
                    "Sync phase 'contents' completed in {:.2f}s",
                    time.perf_counter() - phase_start,
                )

            # =====================================================
            # Events
            # =====================================================

            if sync_events:
                phase_start = time.perf_counter()

                self._notify(
                    phase="events",
                    message="دریافت رویدادها...",
                    current=0,
                    total=1,
                    changes=self._result_changes(result),
                )

                self._sync_events(result, first_sync)

                self._notify(
                    phase="events",
                    message="رویدادها دریافت شد",
                    current=1,
                    total=1,
                    changes=self._result_changes(result),
                )

                logger.info(
                    "Sync phase 'events' completed in {:.2f}s",
                    time.perf_counter() - phase_start,
                )

            # =====================================================
            # Wall
            # =====================================================

            if sync_wall:
                phase_start = time.perf_counter()

                self._notify(
                    phase="wall",
                    message="دریافت wall درس‌ها...",
                    current=0,
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                self._sync_wall(result, first_sync, active_courses)

                self._notify(
                    phase="wall",
                    message="wall درس‌ها دریافت شد",
                    current=len(active_courses),
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                logger.info(
                    "Sync phase 'wall' completed in {:.2f}s",
                    time.perf_counter() - phase_start,
                )

            # =====================================================
            # Schedules (زمان + مکان کلاس)
            # =====================================================

            phase_start = time.perf_counter()

            self._notify(
                phase="schedules",
                message="دریافت برنامه‌ی کلاس‌ها...",
                current=0,
                total=len(active_courses),
            )

            self._sync_schedules(result, active_courses)

            logger.info(
                "Sync phase 'schedules' completed in {:.2f}s",
                time.perf_counter() - phase_start,
            )

            # =====================================================
            # Members
            # =====================================================

            if sync_members:
                phase_start = time.perf_counter()

                self._notify(
                    phase="members",
                    message="دریافت اعضای درس‌ها...",
                    current=0,
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                self._sync_members(result, first_sync, active_courses)

                self._notify(
                    phase="members",
                    message="اعضای درس‌ها دریافت شد",
                    current=len(active_courses),
                    total=len(active_courses),
                    changes=self._result_changes(result),
                )

                logger.info(
                    "Sync phase 'members' completed in {:.2f}s",
                    time.perf_counter() - phase_start,
                )

            # =====================================================
            # Finish
            # =====================================================

            self.setting_repo.set(
                "last_sync",
                datetime.now().isoformat(),
            )

            if first_sync:
                self.setting_repo.set("first_sync", "done")

            result.duration_seconds = time.perf_counter() - start_time

            self._notify(
                phase="done",
                message="Sync کامل شد",
                current=1,
                total=1,
                changes=self._result_changes(result),
            )

            logger.info(
                "Sync completed in {:.2f}s",
                result.duration_seconds,
            )

            return result

        except Exception as exc:
            result.error = str(exc)
            result.duration_seconds = time.perf_counter() - start_time

            logger.exception("Sync failed")

            self._notify(
                phase="error",
                message=f"خطا: {exc}",
                changes=self._result_changes(result),
            )

            return result

    # =============================================================
    # Courses
    # =============================================================

    def _sync_courses(
        self,
        result: SyncResult,
        first_sync: bool,
        courses,
    ) -> None:
        for course in courses:
            old_course = self.course_repo.get_by_id(course.id)
            self.course_repo.save(course)

            if old_course is None:
                result.courses_new += 1

                if not first_sync:
                    self._save_change(
                        change_type=ChangeType.NEW,
                        entity_type=EntityType.COURSE,
                        entity_id=course.id,
                        course_id=course.id,
                        data={"title": course.title},
                    )
            else:
                result.courses_updated += 1

    # =============================================================
    # Contents
    # =============================================================

    def _sync_contents(
        self,
        result: SyncResult,
        first_sync: bool,
        courses,
    ) -> None:
        def fetch(course):
            try:
                contents = self.assistant.get_course_contents(course)
                return course, contents
            except Exception:
                logger.exception(
                    "Failed to sync contents for course {}", course.id
                )
                return course, []

        completed = 0
        total = len(courses)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(fetch, course) for course in courses
            ]

            for future in as_completed(futures):
                course, contents = future.result()
                completed += 1

                for content in contents:
                    old_content = self.content_repo.get_by_id(content.id)
                    self.content_repo.save(content)

                    if old_content is None:
                        result.contents_new += 1

                        if not first_sync:
                            self._save_change(
                                change_type=ChangeType.NEW,
                                entity_type=EntityType.CONTENT,
                                entity_id=content.id,
                                course_id=course.id,
                                data={"title": content.title},
                            )
                    else:
                        result.contents_updated += 1

                self._notify(
                    phase="contents",
                    message=f"محتوای {completed} از {total} درس",
                    current=completed,
                    total=total,
                    changes=self._result_changes(result),
                )

    # =============================================================
    # Events
    # =============================================================

    def _sync_events(
        self,
        result: SyncResult,
        first_sync: bool,
    ) -> None:
        events = self.assistant.get_all_events()

        for event in events:
            old_event = self.event_repo.get_by_id(event.id)
            self.event_repo.save(event)

            if old_event is None:
                result.events_new += 1

                if not first_sync:
                    self._save_change(
                        change_type=ChangeType.NEW,
                        entity_type=EntityType.EVENT,
                        entity_id=event.id,
                        data={"title": event.title},
                    )
            else:
                result.events_updated += 1

    # =============================================================
    # Wall
    # =============================================================

    def _sync_wall(
        self,
        result: SyncResult,
        first_sync: bool,
        courses,
    ) -> None:
        def fetch(course):
            try:
                posts, assignments = self.assistant.get_course_wall(course)
                return course, posts, assignments
            except Exception:
                logger.exception(
                    "Failed to sync wall for course {}", course.id
                )
                return course, [], []

        completed = 0
        total = len(courses)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(fetch, course) for course in courses
            ]

            for future in as_completed(futures):
                course, posts, assignments = future.result()
                completed += 1

                self._sync_posts(result, first_sync, course, posts)
                self._sync_assignments(result, first_sync, course, assignments)

                self._notify(
                    phase="wall",
                    message=f"wall {completed} از {total} درس",
                    current=completed,
                    total=total,
                    changes=self._result_changes(result),
                )

    # =============================================================
    # Posts
    # =============================================================

    def _sync_posts(
        self,
        result: SyncResult,
        first_sync: bool,
        course,
        posts,
    ) -> None:
        for post in posts:
            old_post = self.post_repo.get_by_id(post.id)
            self.post_repo.save(post)

            if old_post is None:
                result.posts_new += 1
            else:
                result.posts_updated += 1

    # =============================================================
    # Assignments
    # =============================================================

    def _sync_assignments(
        self,
        result: SyncResult,
        first_sync: bool,
        course,
        assignments,
    ) -> None:
        for assignment in assignments:
            old_assignment = self.assignment_repo.get_by_id(assignment.id)
            self.assignment_repo.save(assignment)

            if old_assignment is None:
                result.assignments_new += 1
            else:
                result.assignments_updated += 1

    # =============================================================
    # Members
    # =============================================================

    def _sync_members(
        self,
        result: SyncResult,
        first_sync: bool,
        courses,
    ) -> None:
        """Sync اعضای درس‌ها (دانشجو + استاد + پشتیبان)."""

        def fetch(course):
            try:
                collector = MembersCollector(
                    self.assistant.client,
                    course,
                )

                base_url = self.DOMAIN_URLS.get(
                    course.domain,
                    "https://lms4.ui.ac.ir",
                )

                parser = MemberParser(
                    course_id=course.group_id,
                    teacher_name=course.teacher,
                    base_url=base_url,
                )

                members = []

                # === دانشجوها (چند صفحه) ===
                student_pages = collector.collect_all_students()
                for html in student_pages:
                    members.extend(
                        parser.parse(html, is_admin_page=False)
                    )

                # === ادمین‌ها / استادها ===
                admin_html = collector.collect_admins()
                if admin_html:
                    members.extend(
                        parser.parse(admin_html, is_admin_page=True)
                    )

                return course, members

            except Exception:
                logger.exception(
                    "Failed to sync members for course {}", course.id
                )
                return course, []

        completed = 0
        total = len(courses)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(fetch, course) for course in courses
            ]

            for future in as_completed(futures):
                course, members = future.result()
                completed += 1

                for member in members:
                    old_member = self.member_repo.get_by_id(member.id)
                    self.member_repo.save(member)

                    if old_member is None:
                        result.members_new += 1
                    else:
                        result.members_updated += 1

                self._notify(
                    phase="members",
                    message=f"اعضای {completed} از {total} درس",
                    current=completed,
                    total=total,
                    changes=self._result_changes(result),
                )

    def _sync_schedules(self, result: SyncResult, courses) -> None:
        """Sync برنامه‌ی هفتگی (زمان + مکان)."""
        from src.parsers.course_schedule_parser import CourseScheduleParser
        from src.storage.repositories.course_schedule_repo import CourseScheduleRepository
        from concurrent.futures import ThreadPoolExecutor, as_completed

        parser = CourseScheduleParser()
        repo = CourseScheduleRepository(self.db, self.user_id)

        def fetch(course):
            try:
                html = self.assistant.get_course_wall_html(course)
                if not html:
                    return course, None

                schedule = parser.parse(html, course.group_id)
                return course, schedule
            except Exception:
                logger.exception(f"خطا در schedule {course.id}")
                return course, None

        completed = 0
        total = len(courses)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch, c) for c in courses]

            for future in as_completed(futures):
                course, schedule = future.result()
                completed += 1

                if schedule:
                    repo.save(schedule)

                self._notify(
                    phase="schedules",
                    message=f"برنامه {completed} از {total} درس",
                    current=completed,
                    total=total,
                )

    # =============================================================
    # Changes
    # =============================================================

    def _save_change(
        self,
        change_type: ChangeType,
        entity_type: EntityType,
        entity_id: str,
        course_id: str | None = None,
        data: dict | None = None,
    ) -> None:
        """ساخت و ذخیره یک Change با API واقعی Repository."""
        change = Change(
            type=change_type,
            entity_type=entity_type,
            entity_id=entity_id,
            course_id=course_id,
            data=data or {},
        )
        self.change_repo.save(change)