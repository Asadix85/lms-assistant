"""Parser برای صفحه لیست درس‌ها."""

import re

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.models.course import Course
from src.parsers.base import BaseParser
from src.models.course import Course, CourseStatus


class CourseParser(BaseParser):
    """استخراج درس‌ها از HTML /pages/nodeclass.

    ساختار HTML:
    <a href="...">
      <div class="classwig">
        <table class="classtable">
          <tr><td class="coverimg">
            <div class="mastertitle">استاد XXX</div>
          </td></tr>
          <tr><td>
            <h2 class="classtitle">نام درس</h2>
          </td></tr>
          <tr><td class="classdesc">
            <span>کد درس : XXX</span>
          </td></tr>
        </table>
      </div>
    </a>
    """

    def __init__(self, base_url: str = "https://lms4.ui.ac.ir") -> None:
        self.base_url = base_url.rstrip("/")
        self._group_pattern = re.compile(r"/group/(\d+)")
        self._nodeg_pattern = re.compile(r"/nodeg/[^/]+/(\d+)/\d+")
        self._code_pattern = re.compile(r"کد درس\s*:\s*([\d\-]+)")
        self._term_pattern = re.compile(r"(\d+)\s*$")  # عدد آخر = ترم

    def parse(self, html: str) -> list[Course]:
        """Parse کردن HTML و برگرداندن لیست درس‌ها."""
        soup = BeautifulSoup(html, "lxml")

        # پیدا کردن همه لینک‌های درس
        # هر لینک یک div.classwig دارد
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

        # داخل لینک، باید div.classwig باشد
        classwig = link.find("div", class_="classwig")
        if not classwig:
            return None

        # استخراج گروه/شناسه
        group_id = self._extract_group_id(href)
        if not group_id:
            return None

        # استخراج نام درس
        name_el = classwig.find("h2", class_="classtitle")
        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            return None

        # استخراج استاد
        teacher_el = classwig.find("div", class_="mastertitle")
        teacher = teacher_el.get_text(strip=True) if teacher_el else None
        if teacher:
            # حذف "استاد " از ابتدا
            teacher = re.sub(r"^استاد\s+", "", teacher).strip()

        # استخراج کد درس
        desc_el = classwig.find("td", class_="classdesc")
        code = None
        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            code_match = self._code_pattern.search(desc_text)
            if code_match:
                code = code_match.group(1)

        # استخراج ترم (عدد آخر در name)
        term = None
        term_match = self._term_pattern.search(name)
        if term_match:
            term = term_match.group(1)
            # حذف عدد از name
            name = self._term_pattern.sub("", name).strip()

        # ساخت URL کامل
        url = self._make_full_url(href)

        # تشخیص status از HTML
        status = CourseStatus.ACTIVE  # پیش‌فرض
        # چک کردن opacity در classwig (اگر 0.7 بود → finished)
        style = classwig.get("style", "")
        if "opacity:0.7" in style or "opacity: 0.7" in style:
            status = CourseStatus.FINISHED

        # یا چک کردن متن "ترم پایان یافته" در desc
        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            if "ترم پایان یافته" in desc_text:
                status = CourseStatus.FINISHED
            # استخراج code (فقط اگر status active باشد)
            if status == CourseStatus.ACTIVE:
                code_match = self._code_pattern.search(desc_text)
                if code_match:
                    code = code_match.group(1)

        return Course(
            id=group_id,
            name=name,
            url=url,
            group_id=group_id,
            teacher=teacher,
            code=code,
            term=term,
            status=status,
        )

    def _extract_group_id(self, href: str) -> str | None:
        """استخراج group_id از URL.

        پشتیبانی از دو فرمت:
        - /group/139710
        - /nodeg/{token}/140060/2
        """
        # اول /group/
        match = self._group_pattern.search(href)
        if match:
            return match.group(1)

        # بعد /nodeg/
        match = self._nodeg_pattern.search(href)
        if match:
            return match.group(1)

        return None

    def _make_full_url(self, href: str) -> str:
        """ساخت URL کامل."""
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return f"{self.base_url}{href}"
        # نسبی مثل "../group/139710"
        cleaned = href.lstrip("./")
        return f"{self.base_url}/{cleaned}"