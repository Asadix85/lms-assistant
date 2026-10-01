"""سرویس اصلی LMS Assistant: مدیریت login و multi-domain."""

from loguru import logger

from src.collectors.courses import CoursesCollector
from src.core.auth import LMSAuth
from src.core.http_client import LMSHttpClient
from src.models.course import Course
from src.parsers.courses import CourseParser


class LMSAssistant:
    """مدیریت کامل LMS.

    جریان کار:
    1. login به lms4 (دامنه‌ی دانشکده)
    2. GET /pages/nodeclass → لیست دروس (شامل nodeg برای lms3/lms5)
    3. برای هر nodeg → فعال‌سازی session دامنه‌ی مقصد
    4. حالا می‌توانیم به همه دامنه‌ها دسترسی داشته باشیم
    """

    BASE_DOMAIN = "lms4"

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        # Client روی lms4
        self.client = LMSHttpClient(base_url="https://lms4.ui.ac.ir")
        self.auth = LMSAuth(self.client)
        self.course_parser = CourseParser(base_url="https://lms4.ui.ac.ir")

        # دامنه‌های فعال
        self.active_domains: set[str] = set()

    # === Login ===

    def login(self) -> bool:
        """Login به دامنه‌ی اصلی (lms4)."""
        success = self.auth.login(self.username, self.password)
        if success:
            self.active_domains.add("lms4")
            logger.info("✅ Login به lms4 موفق")
        return success

    @property
    def is_authenticated(self) -> bool:
        """آیا login کرده‌ایم؟"""
        return self.auth.is_authenticated

    @property
    def user_id(self) -> str | None:
        """شناسه کاربر."""
        return self.auth.user_id

    # === Activate Domain via nodeg ===

    def activate_domain(self, nodeg_url: str, domain: str) -> bool:
        """فعال‌سازی session دامنه‌ی دیگر از طریق nodeg."""
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
        """دریافت همه درس‌ها و فعال‌سازی دامنه‌ها."""
        # ۱. Collect
        collector = CoursesCollector(self.client)
        html = collector.collect()

        # ۲. Parse
        courses = self.course_parser.parse(html)

        # ۳. فعال‌سازی دامنه‌های nodeg
        activated: set[str] = set()
        for c in courses:
            if c.nodeg_url and c.domain not in activated:
                self.activate_domain(c.nodeg_url, c.domain)
                activated.add(c.domain)

        return courses

    def get_active_courses(self) -> list[Course]:
        """فقط دروس ترم جاری."""
        return [c for c in self.get_all_courses() if c.is_active]

    # === Lifecycle ===

    def close(self) -> None:
        """بستن client."""
        self.client.close()

    def __enter__(self) -> "LMSAssistant":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        status = "authenticated" if self.is_authenticated else "not authenticated"
        domains = ", ".join(sorted(self.active_domains)) or "none"
        return f"LMSAssistant({status}, domains=[{domains}])"