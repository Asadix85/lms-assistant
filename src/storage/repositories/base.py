"""Base Repository — همه queryها به یک user_id محدود می‌شوند."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.storage.database import Database


class BaseRepository(ABC):
    """کلاس پایه برای repositoryهای چندکاربره."""

    TABLE_NAME: str = ""

    def __init__(self, db: Database, user_id: str | None = None) -> None:
        # دسکتاپ تک‌کاربره: "__local__" — وب حتماً user واقعی می‌فرستد
        self.db = db
        self.user_id = user_id or "__local__"

    @abstractmethod
    def save(self, item: Any) -> None:
        ...

    @abstractmethod
    def get_by_id(self, item_id: str) -> Any | None:
        ...

    @abstractmethod
    def get_all(self) -> list[Any]:
        ...

    def count(self) -> int:
        result = self.db.fetch_one(
            f"SELECT COUNT(*) as n FROM {self.TABLE_NAME} WHERE user_id = ?",
            (self.user_id,),
        )
        return result["n"] if result else 0

    def exists(self, item_id: str) -> bool:
        return self.get_by_id(item_id) is not None
