"""Base Repository."""

from abc import ABC, abstractmethod
from typing import Any

from src.storage.database import Database


class BaseRepository(ABC):
    """کلاس پایه برای همه repositoryها."""

    TABLE_NAME: str = ""

    def __init__(self, db: Database) -> None:
        self.db = db

    @abstractmethod
    def save(self, item: Any) -> None:
        """ذخیره یک آیتم."""
        ...

    @abstractmethod
    def get_by_id(self, item_id: str) -> Any | None:
        """خواندن یک آیتم با ID."""
        ...

    @abstractmethod
    def get_all(self) -> list[Any]:
        """خواندن همه آیتم‌ها."""
        ...

    def count(self) -> int:
        """تعداد آیتم‌ها."""
        result = self.db.fetch_one(f"SELECT COUNT(*) as n FROM {self.TABLE_NAME}")
        return result["n"] if result else 0

    def exists(self, item_id: str) -> bool:
        """آیا آیتم وجود دارد؟"""
        return self.get_by_id(item_id) is not None