"""Collector برای اعضای درس (با pagination هوشمند)."""

import re

from loguru import logger

from src.collectors.base import BaseCollector
from src.models.course import Course


class MembersCollector(BaseCollector):
    """دریافت لیست اعضا از widget."""

    WIDGET_CONTENT_ID = 1517
    MAX_PAGES = 20

    # الگوی ID عضو
    MEMBER_ID_PATTERN = re.compile(r"group_member_(\d+)")

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
        """دریافت همه‌ی صفحات دانشجویان (با تشخیص توقف هوشمند).

        استراتژی توقف:
        1. HTML خیلی کوتاه → توقف
        2. هیچ ID جدیدی در صفحه نیست → توقف (صفحه تکراری)
        3. به max_pages رسیدیم → توقف
        """
        pages: list[str] = []
        seen_ids: set[str] = set()

        for page in range(1, max_pages + 1):
            html = self.collect_students(page=page)

            # ۱. HTML خیلی کوتاه
            if len(html) < 3000:
                logger.debug(
                    f"  توقف: صفحه {page} کوتاه ({len(html)} کاراکتر)"
                )
                break

            # ۲. استخراج IDها
            page_ids = set(self.MEMBER_ID_PATTERN.findall(html))

            # اگه ID جدیدی نیست → توقف
            new_ids = page_ids - seen_ids
            if not new_ids:
                logger.debug(
                    f"  توقف: صفحه {page} تکراری (no new IDs)"
                )
                break

            seen_ids.update(page_ids)
            pages.append(html)

            logger.debug(
                f"  صفحه {page}: {len(page_ids)} عضو "
                f"({len(new_ids)} جدید، کل: {len(seen_ids)})"
            )

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