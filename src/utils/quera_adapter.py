"""آداپتور QueraAssignment → Assignment برای استفاده در widgetها."""

from datetime import datetime

from src.models.assignment import Assignment
from src.models.quera_assignment import QueraAssignment
from src.models.event import Event, EventType


QUERA_PREFIX = "quera_"


def quera_to_assignment(q: QueraAssignment) -> Assignment:
    """تبدیل QueraAssignment به Assignment (برای widgetهای موجود)."""
    # ددلاین: naive local
    deadline = None
    if q.finish_time:
        if q.finish_time.tzinfo is not None:
            deadline = q.finish_time.astimezone().replace(tzinfo=None)
        else:
            deadline = q.finish_time

    return Assignment(
        id=f"{QUERA_PREFIX}{q.id}",
        course_id=f"{QUERA_PREFIX}{q.course_name}",  # synthetic
        title=q.name,
        description="",
        deadline=deadline,
        deadline_jalali=None,
        is_new=False,
        response_count=q.submitted_count,
    )


def quera_to_event(q: QueraAssignment) -> Event | None:
    """تبدیل QueraAssignment به Event (برای نمایش در تقویم)."""
    if not q.finish_time:
        return None

    # ددلاین به عنوان Event
    finish = q.finish_time
    if finish.tzinfo is not None:
        finish = finish.astimezone().replace(tzinfo=None)

    return Event(
        id=f"{QUERA_PREFIX}{q.id}",
        course_id=f"{QUERA_PREFIX}{q.course_name}",
        title=q.name,
        event_type=EventType.DEADLINE,  # ← نوع deadline
        start_at=finish,
    )


def is_quera_item(item) -> bool:
    """آیا این آیتم از Quera هست؟"""
    return str(getattr(item, "id", "")).startswith(QUERA_PREFIX)


def get_quera_course_name(synthetic_id: str) -> str:
    """گرفتن اسم درس از synthetic_id."""
    if synthetic_id.startswith(QUERA_PREFIX):
        return synthetic_id[len(QUERA_PREFIX):]
    return synthetic_id