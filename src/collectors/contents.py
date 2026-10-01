"""Collector برای محتوای درس."""

from loguru import logger

from src.collectors.base import BaseCollector


class ContentsCollector(BaseCollector):
    """دریافت لیست محتوای یک درس از /group/index/listofcontent/."""

    def __init__(self, client, course_id: str) -> None:
        super().__init__(client)
        self.course_id = course_id

    def collect(self) -> str:
        """GET صفحه listofcontent و برگرداندن HTML."""
        path = f"/group/index/listofcontent/?group_id={self.course_id}"
        logger.info(f"دریافت محتوای درس {self.course_id}")
        response = self.client.get(path)
        response.raise_for_status()
        logger.debug(f"  → {len(response.text)} کاراکتر")
        return response.text