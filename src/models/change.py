"""مدل Change (تغییرات بین Syncها)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    """نوع تغییر."""
    NEW = "new"
    UPDATED = "updated"
    REMOVED = "removed"


class EntityType(str, Enum):
    """نوع موجودیت."""
    COURSE = "course"
    CONTENT = "content"
    EVENT = "event"


@dataclass
class Change:
    """یک تغییر."""

    type: ChangeType
    entity_type: EntityType
    entity_id: str
    course_id: str | None = None
    data: dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return (
            f"Change({self.type.value} {self.entity_type.value} "
            f"id={self.entity_id!r})"
        )