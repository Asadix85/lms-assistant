"""مدل Quera Course (کلاس)."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QueraCourse:
    """یه کلاس Quera."""

    id: str
    name: str
    url: str
    teacher: str = ""
    is_active: bool = True
    assignments_count: int = 0

    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    @property
    def synthetic_id(self) -> str:
        return f"quera_{self.id}"

    def __repr__(self) -> str:
        return f"QueraCourse(id={self.id!r}, name={self.name[:30]!r})"