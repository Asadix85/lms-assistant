"""سرویس اصلی LMS Assistant: مدیریت login و multi-domain."""

from loguru import logger

from src.collectors.contents import ContentsCollector
from src.collectors.courses import CoursesCollector
from src.collectors.events import EventsCollector
from src.collectors.wall import WallCollector
from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient
from src.models.assignment import Assignment
from src.models.content import Content
from src.models.course import Course
from src.models.event import Event
from src.models.post import Post
from src.parsers.contents import ContentParser
from src.parsers.courses import CourseParser
from src.parsers.events import EventParser
from src.parsers.wall import WallParser


class LMSAssistant:
    """مدیریت کامل LMS: login + multi-domain + collect."""

    DOMAIN_URLS = {
        "lms3": "https://lms3.ui.ac.ir",
        "lms4": "https://lms4.ui.ac.ir",
        "lms5": "https://lms5.ui.ac.ir",
    }

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self.client = LMSHttpClient(base_url="https://lms4.ui.ac.ir")
        self.auth = LMSAuth(self.client)
        self.course_parser = CourseParser(base_url="https://lms4.ui.ac.ir")
        self.event_parser = EventParser(base_url="https://lms4.ui.ac.ir")

        self.active_domains: set[str] = set()

    # === Login ===

    def login(self) -> bool:
        success = self.auth.login(self.username, self.password)
        if success:
            self.active_domains.add("lms4")
            logger.info("✅ Login به lms4 موفق")
        return success

    @property
    def is_authenticated(self) -> bool:
        return self.auth.is_authenticated

    @property
    def user_id(self) -> str | None:
        return self.auth.user_id

    # === Activate Domain ===

    def activate_domain(self, nodeg_url: str, domain: str) -> bool:
        if domain in self.active_domains:
            return True

        try:
            logger.debug(f"فعال‌سازی دامنه {domain} از طریق nodeg...")
            r = self.client.get(nodeg_url, timeout=30)
            if r.status_code == 200:
                self.active_domains.add(domain)
                logger.info(f"✅ دامنه {domain} فعال شد")
                return True
            logger.warning(f"❌ فعال‌سازی {domain} ناموفق: {r.status_code}")
            return False
        except Exception as e:
            logger.error(f"خطا در فعال‌سازی {domain}: {e}")
            return False

    # === Courses ===

    def get_all_courses(self) -> list[Course]:
        collector = CoursesCollector(self.client)
        html = collector.collect()
        courses = self.course_parser.parse(html)

        activated: set[str] = set()
        for c in courses:
            if c.nodeg_url and c.domain not in activated:
                self.activate_domain(c.nodeg_url, c.domain)
                activated.add(c.domain)

        return courses

    def get_active_courses(self) -> list[Course]:
        return [c for c in self.get_all_courses() if c.is_active]

    # === Contents ===

    def get_course_contents(self, course: Course) -> list[Content]:
        if course.domain not in self.active_domains:
            if course.nodeg_url:
                self.activate_domain(course.nodeg_url, course.domain)
            else:
                logger.warning(f"دامنه {course.domain} فعال نیست")
                return []

        collector = ContentsCollector(self.client, course=course)
        html = collector.collect()

        base_url = self.DOMAIN_URLS.get(course.domain, "https://lms4.ui.ac.ir")
        parser = ContentParser(course_id=course.group_id, base_url=base_url)
        return parser.parse(html)

    def get_all_contents(self) -> dict[str, list[Content]]:
        courses = self.get_active_courses()
        result: dict[str, list[Content]] = {}

        for c in courses:
            try:
                contents = self.get_course_contents(c)
                if contents:
                    result[c.id] = contents
            except Exception as e:
                logger.error(f"خطا در محتوای {c.name}: {e}")

        return result

    # === Events ===

    def get_all_events(self) -> list[Event]:
        collector = EventsCollector(self.client)
        html = collector.collect()
        return self.event_parser.parse(html)

    # === Wall (Posts + Assignments) ===

    def get_course_wall(
        self, course: Course
    ) -> tuple[list[Post], list[Assignment]]:
        """دریافت Postها و Assignmentهای یک درس.

        Returns:
            (posts, assignments)
        """
        # اطمینان از فعال بودن دامنه
        if course.domain not in self.active_domains:
            if course.nodeg_url:
                self.activate_domain(course.nodeg_url, course.domain)
            else:
                logger.warning(f"دامنه {course.domain} فعال نیست")
                return [], []

        try:
            collector = WallCollector(self.client, course=course)
            html = collector.collect()

            base_url = self.DOMAIN_URLS.get(course.domain, "https://lms4.ui.ac.ir")
            parser = WallParser(course_id=course.group_id, base_url=base_url)
            return parser.parse(html)
        except Exception as e:
            logger.error(f"خطا در wall {course.name}: {e}")
            return [], []

    def get_all_wall_data(
        self,
    ) -> tuple[dict[str, list[Post]], dict[str, list[Assignment]]]:
        """دریافت wall همه دروس فعال.

        Returns:
            (posts_by_course, assignments_by_course)
        """
        courses = self.get_active_courses()
        posts_by_course: dict[str, list[Post]] = {}
        assignments_by_course: dict[str, list[Assignment]] = {}

        for c in courses:
            posts, assignments = self.get_course_wall(c)
            if posts:
                posts_by_course[c.id] = posts
            if assignments:
                assignments_by_course[c.id] = assignments

        return posts_by_course, assignments_by_course

    # === Lifecycle ===

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "LMSAssistant":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        status = "authenticated" if self.is_authenticated else "not authenticated"
        domains = ", ".join(sorted(self.active_domains)) or "none"
        return f"LMSAssistant({status}, domains=[{domains}])"