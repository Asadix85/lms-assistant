"""Collector برای اعضای درس (با pagination)."""

from loguru import logger

from src.collectors.base import BaseCollector
from src.models.course import Course


class MembersCollector(BaseCollector):
    """دریافت لیست اعضا از widget."""

    WIDGET_CONTENT_ID = 1517
    MAX_PAGES = 20

    def __init__(self, client, course: Course) -> None:
        super().__init__(client)
        self.course = course

    def collect(self) -> str:
        return self.collect_students(page=1)

    def collect_students(self, page: int = 1) -> str:
        return self._fetch_page(page_type="student", page=page)

    def collect_admins(self, page: int = 1) -> str:
        return self._fetch_page(page_type="admin", page=page)

    def collect_all_students(self, max_pages: int = MAX_PAGES) -> list[str]:
        """دریافت همه‌ی صفحات دانشجویان."""
        pages: list[str] = []

        for page in range(1, max_pages + 1):
            html = self.collect_students(page=page)
            if len(html) < 3000:
                break
            pages.append(html)

        return pages

    def _fetch_page(self, page_type: str, page: int = 1) -> str:
        path = f"/widget/index/content_id/{self.WIDGET_CONTENT_ID}"
        subject = f"group_{self.course.group_id}"

        if page_type == "student":
            data = {
                "format": "html",
                "page_type": "student",
                "subject": subject,
                "pageStudent": str(page),
                "searchstudent": "",
            }
        else:
            data = {
                "format": "html",
                "page_type": "admin",
                "subject": subject,
                "pageAdmin": str(page),
                "searchAdmin": "",
            }

        logger.debug(f"دریافت {page_type} صفحه {page}")
        response = self.client.post(path, data=data)
        response.raise_for_status()
        return response.text