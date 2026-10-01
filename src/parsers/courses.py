"""Parser برای صفحه لیست درس‌ها."""

import re

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.models.course import Course, CourseStatus
from src.parsers.base import BaseParser


class CourseParser(BaseParser):
    """استخراج درس‌ها از HTML /pages/nodeclass.

    پشتیبانی از دو فرمت URL:
    - /group/{id}                      → lms4
    - /nodeg/{token}/{id}/{n}          → lms3/lms5
    """

    def __init__(self, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.base_url = base_url.rstrip("/")
        self._group_pattern = re.compile(r"/group/(\d+)")
        self._nodeg_pattern = re.compile(r"/nodeg/[^/]+/(\d+)/\d+")
        self._nodeg_domain_pattern = re.compile(r"https?://(lms\d)\.ui\.ac\.ir")
        self._code_pattern = re.compile(r"کد درس\s*:\s*([\d\-]+)")
        self._term_pattern = re.compile(r"(\d+)\s*$")

    def parse(self, html: str) -> list[Course]:
        """Parse کردن HTML و برگرداندن لیست درس‌ها."""
        soup = BeautifulSoup(html, "lxml")

        links = soup.find_all("a", href=True)
        courses: list[Course] = []
        seen_ids: set[str] = set()

        for link in links:
            course = self._parse_course_link(link)
            if course and course.id not in seen_ids:
                courses.append(course)
                seen_ids.add(course.id)

        logger.info(f"{len(courses)} درس استخراج شد")
        return courses

    def _parse_course_link(self, link: Tag) -> Course | None:
        """تبدیل یک تگ <a> به Course (اگر درس باشد)."""
        href = link.get("href", "")
        if not href:
            return None

        # داخل لینک باید div.classwig باشد
        classwig = link.find("div", class_="classwig")
        if not classwig:
            return None

        # استخراج دامنه و group_id
        domain, group_id = self._extract_domain_and_id(href)
        if not group_id:
            return None

        # nodeg_url (اگر از دامنه‌ی دیگر باشد)
        nodeg_url = href if "/nodeg/" in href else None

        # استخراج نام درس
        name_el = classwig.find("h2", class_="classtitle")
        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            return None

        # استخراج استاد
        teacher_el = classwig.find("div", class_="mastertitle")
        teacher = teacher_el.get_text(strip=True) if teacher_el else None
        if teacher:
            teacher = re.sub(r"^استاد\s+", "", teacher).strip()

        # استخراج کد درس و status
        desc_el = classwig.find("td", class_="classdesc")
        code = None
        status = CourseStatus.ACTIVE

        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            if "ترم پایان یافته" in desc_text:
                status = CourseStatus.FINISHED
            else:
                code_match = self._code_pattern.search(desc_text)
                if code_match:
                    code = code_match.group(1)

        # استخراج ترم
        term = None
        term_match = self._term_pattern.search(name)
        if term_match:
            term = term_match.group(1)
            name = self._term_pattern.sub("", name).strip()

        # ساخت URL کامل
        url = self._make_full_url(href, domain)

        return Course(
            id=group_id,
            name=name,
            url=url,
            group_id=group_id,
            domain=domain,
            nodeg_url=nodeg_url,
            teacher=teacher,
            code=code,
            term=term,
            status=status,
        )

    def _extract_domain_and_id(self, href: str) -> tuple[str, str | None]:
        """استخراج دامنه و group_id از URL.

        Returns:
            (domain, group_id) — مثلاً ("lms3", "140060") یا ("lms4", "139710")
        """
        # nodeg → lms3 یا lms5
        if "/nodeg/" in href:
            domain_match = self._nodeg_domain_pattern.search(href)
            domain = domain_match.group(1) if domain_match else "lms3"

            id_match = self._nodeg_pattern.search(href)
            group_id = id_match.group(1) if id_match else None

            return domain, group_id

        # /group/ → lms4
        match = self._group_pattern.search(href)
        if match:
            return "lms4", match.group(1)

        return "lms4", None

    def _make_full_url(self, href: str, domain: str) -> str:
        """ساخت URL کامل."""
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return f"{self.base_url}{href}"

        # نسبی مثل "../group/139710"
        cleaned = href.lstrip("./")
        return f"{self.base_url}/{cleaned}"