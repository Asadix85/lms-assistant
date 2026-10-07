"""آداپتور QueraAssignment → Assignment برای widgetهای موجود."""

from datetime import datetime

from src.models.assignment import Assignment
from src.models.quera_assignment import QueraAssignment


QUERA_PREFIX = "quera_"


def quera_to_assignment(q: QueraAssignment) -> Assignment:
    """تبدیل QueraAssignment به Assignment."""
    # deadline → naive local
    deadline = None
    if q.finish_time:
        if q.finish_time.tzinfo is not None:
            deadline = q.finish_time.astimezone().replace(tzinfo=None)
        else:
            deadline = q.finish_time

    return Assignment(
        id=f"{QUERA_PREFIX}{q.id}",
        course_id=f"{QUERA_PREFIX}{q.course_name}",
        title=q.name,
        description="",
        deadline=deadline,
        deadline_jalali=None,
        is_new=False,
        response_count=q.submitted_count,
    )


def is_quera_item(item) -> bool:
    """آیا از Quera هست؟"""
    return str(getattr(item, "id", "")).startswith(QUERA_PREFIX)


def quera_course_label(synthetic_id: str) -> str:
    """گرفتن نام درس Quera از synthetic_id."""
    if synthetic_id.startswith(QUERA_PREFIX):
        return f"🎯 {synthetic_id[len(QUERA_PREFIX):]}"
    return synthetic_id