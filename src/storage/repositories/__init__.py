"""Repositories."""

from src.storage.repositories.assignment_repo import AssignmentRepository
from src.storage.repositories.change_repo import ChangeRepository
from src.storage.repositories.content_repo import ContentRepository
from src.storage.repositories.course_repo import CourseRepository
from src.storage.repositories.event_repo import EventRepository
from src.storage.repositories.post_repo import PostRepository
from src.storage.repositories.setting_repo import SettingRepository
from src.storage.repositories.member_repo import MemberRepository
from src.storage.repositories.quera_repo import (
    QueraAssignmentRepository,
    QueraCourseRepository,
)

__all__ = [
    "AssignmentRepository",
    "ChangeRepository",
    "ContentRepository",
    "CourseRepository",
    "EventRepository",
    "PostRepository",
    "SettingRepository",
    "MemberRepository",
    "QueraAssignmentRepository",
    "QueraCourseRepository",
]