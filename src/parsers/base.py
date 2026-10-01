"""Base Parser."""

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """کلاس پایه برای همه parserها."""

    @abstractmethod
    def parse(self, html: str) -> list[Any]:
        """تبدیل HTML به لیست مدل‌ها.

        Args:
            html: محتوای HTML

        Returns:
            لیست مدل‌های parse شده
        """
        ...