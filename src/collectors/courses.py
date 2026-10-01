"""Collector برای درس‌ها."""

from loguru import logger

from config.constants import COURSES_PATH
from src.collectors.base import BaseCollector


class CoursesCollector(BaseCollector):
    """دریافت لیست درس‌ها از /pages/nodeclass."""

    def collect(self) -> str:
        """GET /pages/nodeclass و برگرداندن HTML."""
        logger.info(f"دریافت لیست درس‌ها از {COURSES_PATH}")
        response = self.client.get(COURSES_PATH)
        response.raise_for_status()
        logger.debug(f"  → {len(response.text)} کاراکتر")
        return response.text