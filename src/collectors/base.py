"""Base Collector."""

from abc import ABC, abstractmethod

from src.core.http_client import LMSHttpClient


class BaseCollector(ABC):
    """کلاس پایه برای همه collectorها."""

    def __init__(self, client: LMSHttpClient) -> None:
        self.client = client

    @abstractmethod
    def collect(self) -> str:
        """دریافت HTML خام از LMS.

        Returns:
            HTML به‌صورت رشته
        """
        ...