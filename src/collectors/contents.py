"""Collector برای محتوای درس (پشتیبانی از multi-domain)."""

from loguru import logger

from src.collectors.base import BaseCollector
from src.models.course import Course


class ContentsCollector(BaseCollector):
    """دریافت محتوای یک درس از /group/index/listofcontent/.

    از دامنه‌ی خود درس استفاده می‌کند:
    - lms3 → https://lms3.ui.ac.ir
    - lms4 → https://lms4.ui.ac.ir
    - lms5 → https://lms5.ui.ac.ir
    """

    DOMAIN_URLS = {
        "lms3": "https://lms3.ui.ac.ir",
        "lms4": "https://lms4.ui.ac.ir",
        "lms5": "https://lms5.ui.ac.ir",
    }

    def __init__(self, client, course: Course) -> None:
        """Args:
            client: LMSHttpClient (با session مشترک)
            course: درس مورد نظر
        """
        super().__init__(client)
        self.course = course

    def collect(self) -> str:
        """GET صفحه listofcontent از دامنه‌ی درس."""
        base_url = self.DOMAIN_URLS.get(self.course.domain)
        if not base_url:
            raise ValueError(f"دامنه نامعتبر: {self.course.domain}")

        path = f"/group/index/listofcontent/?group_id={self.course.group_id}"
        url = f"{base_url}{path}"

        logger.info(f"دریافت محتوای درس {self.course.name} ({self.course.domain})")

        response = self.client.get(url)
        response.raise_for_status()

        logger.debug(f"  → {len(response.text)} کاراکتر")
        return response.text