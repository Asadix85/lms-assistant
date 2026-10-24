"""Schemaهای Pydantic برای API وب (تبدیل dataclass‌ها به JSON)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# === Helpers ===

def _dt(value: datetime | None) -> str | None:
    """تبدیل datetime به ISO-8601 string."""
    return value.isoformat(sep=" ", timespec="seconds") if value else None


# === LMS ===


class CourseOut(BaseModel):
    id: str
    name: str
    url: str
    group_id: str
    domain: str
    nodeg_url: str | None = None
    teacher: str | None = None
    code: str | None = None
    term: str | None = None
    status: str
    is_new: bool = False

    @classmethod
    def from_model(cls, c: Any) -> "CourseOut":
        return cls(
            id=c.id,
            name=c.name,
            url=c.url,
            group_id=c.group_id,
            domain=c.domain,
            nodeg_url=c.nodeg_url,
            teacher=c.teacher,
            code=c.code,
            term=c.term,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            is_new=getattr(c, "is_new", False),
        )


class ContentOut(BaseModel):
    id: str
    course_id: str
    title: str
    url: str
    content_type: str
    filename: str
    last_seen_at: str | None = None

    @classmethod
    def from_model(cls, c: Any) -> "ContentOut":
        return cls(
            id=c.id,
            course_id=c.course_id,
            title=c.title,
            url=c.url,
            content_type=c.content_type,
            filename=c.filename,
            last_seen_at=_dt(getattr(c, "last_seen_at", None)),
        )


class EventOut(BaseModel):
    id: str
    course_id: str | None
    title: str
    event_type: str
    url: str | None
    start_at: str | None
    end_at: str | None
    description: str | None
    is_new: bool

    @classmethod
    def from_model(cls, e: Any) -> "EventOut":
        return cls(
            id=e.id,
            course_id=e.course_id,
            title=e.title,
            event_type=e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            url=e.url,
            start_at=_dt(e.start_at),
            end_at=_dt(e.end_at),
            description=e.description,
            is_new=e.is_new,
        )


class PostOut(BaseModel):
    id: str
    course_id: str
    author: str
    author_id: str
    text: str
    posted_at: str | None
    posted_at_jalali: str | None
    post_url: str | None
    is_new: bool

    @classmethod
    def from_model(cls, p: Any) -> "PostOut":
        return cls(
            id=p.id,
            course_id=p.course_id,
            author=p.author,
            author_id=p.author_id,
            text=p.text,
            posted_at=_dt(p.posted_at),
            posted_at_jalali=p.posted_at_jalali,
            post_url=p.post_url,
            is_new=p.is_new,
        )


class AssignmentOut(BaseModel):
    id: str
    course_id: str
    title: str
    description: str
    start_at: str | None
    deadline: str | None
    deadline_jalali: str | None
    submit_url: str | None
    view_url: str | None
    response_count: int
    is_new: bool
    is_manual: bool
    is_done: bool
    is_expired: bool

    @classmethod
    def from_model(cls, a: Any) -> "AssignmentOut":
        return cls(
            id=a.id,
            course_id=a.course_id,
            title=a.title,
            description=a.description,
            start_at=_dt(a.start_at),
            deadline=_dt(a.deadline),
            deadline_jalali=a.deadline_jalali,
            submit_url=a.submit_url,
            view_url=a.view_url,
            response_count=a.response_count,
            is_new=a.is_new,
            is_manual=a.is_manual,
            is_done=a.is_done,
            is_expired=a.is_expired,
        )


class MemberOut(BaseModel):
    id: str
    course_id: str
    name: str
    profile_url: str
    member_type: str

    @classmethod
    def from_model(cls, m: Any) -> "MemberOut":
        return cls(
            id=m.id,
            course_id=m.course_id,
            name=m.name,
            profile_url=m.profile_url,
            member_type=m.member_type.value if hasattr(m.member_type, "value") else str(m.member_type),
        )


class ChangeOut(BaseModel):
    type: str
    entity_type: str
    entity_id: str
    course_id: str | None
    data: dict
    detected_at: str | None

    @classmethod
    def from_model(cls, ch: Any) -> "ChangeOut":
        return cls(
            type=ch.type.value if hasattr(ch.type, "value") else str(ch.type),
            entity_type=ch.entity_type.value if hasattr(ch.entity_type, "value") else str(ch.entity_type),
            entity_id=ch.entity_id,
            course_id=ch.course_id,
            data=ch.data or {},
            detected_at=_dt(ch.detected_at),
        )


# === Quera ===


class QueraProblemOut(BaseModel):
    id: str
    name: str
    type: str
    submission_score: float | None
    state: str
    is_submitted: bool

    @classmethod
    def from_model(cls, p: Any) -> "QueraProblemOut":
        return cls(
            id=p.id,
            name=p.name,
            type=p.type,
            submission_score=p.submission_score,
            state=p.state,
            is_submitted=p.is_submitted,
        )


class QueraAssignmentOut(BaseModel):
    id: str
    name: str
    course_name: str
    finish_time: str | None
    problems: list[QueraProblemOut]
    problems_count: int
    is_manual: bool
    is_done: bool

    @classmethod
    def from_model(cls, a: Any) -> "QueraAssignmentOut":
        return cls(
            id=a.id,
            name=a.name,
            course_name=a.course_name,
            finish_time=_dt(a.finish_time),
            problems=[QueraProblemOut.from_model(p) for p in a.problems],
            problems_count=a.problems_count,
            is_manual=a.is_manual,
            is_done=a.is_done,
        )


class QueraCourseOut(BaseModel):
    id: str
    name: str
    url: str | None = None

    @classmethod
    def from_model(cls, c: Any) -> "QueraCourseOut":
        return cls(
            id=str(getattr(c, "id", "")),
            name=getattr(c, "name", ""),
            url=getattr(c, "url", None),
        )


# === Auth / Sync ===


class LoginRequest(BaseModel):
    lms_username: str = ""
    lms_password: str = ""
    quera_username: str = ""
    quera_password: str = ""


class SessionStatus(BaseModel):
    lms_logged_in: bool
    quera_logged_in: bool
    full_name: str | None = None
    username: str | None = None


class SyncProgressOut(BaseModel):
    phase: str
    phase_index: int
    total_phases: int
    current: int
    total: int
    message: str
    percent: int
    elapsed: float
    changes: dict[str, int]


class SyncResultOut(BaseModel):
    ok: bool
    is_first_sync: bool
    duration_seconds: float
    error: str | None
    total_new: int
    total_updated: int
    total_removed: int
    counts: dict[str, int]
    summary: str

from pydantic import BaseModel

class LocationOut(BaseModel):
    text: str
    faculty: str
    building: str
    lat: float
    lng: float

class SessionOut(BaseModel):
    weekday: str
    start_time: str
    end_time: str
    location_text: str
    faculty: str
    building: str
    lat: float
    lng: float