"""Collector برای رویدادها (تقویم)."""

from loguru import logger

from src.collectors.base import BaseCollector


class EventsCollector(BaseCollector):
    """دریافت رویدادها از /pages/calendar."""

    CALENDAR_PATH = "/pages/calendar"

    def collect(self) -> str:
        """GET /pages/calendar و برگرداندن HTML."""
        logger.info("دریافت تقویم رویدادها")
        response = self.client.get(self.CALENDAR_PATH)
        response.raise_for_status()
        logger.debug(f"  → {len(response.text)} کاراکتر")
        return response.text