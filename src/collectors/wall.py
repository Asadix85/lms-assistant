"""Collector برای wall درس."""

from loguru import logger

from src.collectors.base import BaseCollector
from src.models.course import Course


class WallCollector(BaseCollector):
    """دریافت wall یک درس."""

    DOMAIN_URLS = {
        "lms3": "https://lms3.ui.ac.ir",
        "lms4": "https://lms4.ui.ac.ir",
        "lms5": "https://lms5.ui.ac.ir",
    }

    def __init__(self, client, course: Course) -> None:
        super().__init__(client)
        self.course = course

    def collect(self) -> str:
        base_url = self.DOMAIN_URLS.get(self.course.domain)
        if not base_url:
            raise ValueError(f"دامنه نامعتبر: {self.course.domain}")

        path = f"/group/{self.course.group_id}"
        url = f"{base_url}{path}"

        logger.info(f"دریافت wall درس {self.course.name} ({self.course.domain})")
        response = self.client.get(url)
        response.raise_for_status()
        logger.debug(f"  → {len(response.text)} کاراکتر")
        return response.text