"""Router داده‌های LMS: درس‌ها، محتوا، رویدادها، پست‌ها، تکالیف، اعضا، تغییرات و داشبورد."""

from fastapi import APIRouter, HTTPException, Request

from src.storage.repositories import (
    AssignmentRepository,
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
)
from src.web.schemas import (
    AssignmentOut,
    ChangeOut,
    ContentOut,
    CourseOut,
    EventOut,
    MemberOut,
    PostOut,
)

router = APIRouter()


def _repos(request: Request):
    db = request.app.state.db
    return {
        "courses": CourseRepository(db),
        "contents": ContentRepository(db),
        "events": EventRepository(db),
        "posts": PostRepository(db),
        "assignments": AssignmentRepository(db),
        "members": MemberRepository(db),
        "changes": ChangeRepository(db),
    }


# === Dashboard ===


@router.get("/dashboard")
async def dashboard(request: Request) -> dict:
    r = _repos(request)
    upcoming_events = r["events"].get_upcoming(limit=8)
    upcoming_assignments = r["assignments"].get_upcoming(limit=8)
    recent_posts = r["posts"].get_all()[:8]
    recent_changes = r["changes"].get_recent(limit=10)

    return {
        "stats": {
            "courses": r["courses"].count(),
            "active_courses": len(r["courses"].get_active()),
            "contents": r["contents"].count(),
            "events": r["events"].count(),
            "posts": r["posts"].count(),
            "assignments": r["assignments"].count(),
            "pending_assignments": sum(
                1 for a in r["assignments"].get_all() if not a.is_done
            ),
        },
        "upcoming_events": [EventOut.from_model(e) for e in upcoming_events],
        "upcoming_assignments": [
            AssignmentOut.from_model(a) for a in upcoming_assignments
        ],
        "recent_posts": [PostOut.from_model(p) for p in recent_posts],
        "recent_changes": [ChangeOut.from_model(c) for c in recent_changes],
    }


# === Courses ===


@router.get("/courses", response_model=list[CourseOut])
async def list_courses(request: Request, active_only: bool = False) -> list[CourseOut]:
    repo = CourseRepository(request.app.state.db)
    courses = repo.get_active() if active_only else repo.get_all()
    return [CourseOut.from_model(c) for c in courses]


@router.get("/courses/{course_id}", response_model=CourseOut)
async def get_course(request: Request, course_id: str) -> CourseOut:
    repo = CourseRepository(request.app.state.db)
    course = repo.get_by_id(course_id)
    if not course:
        raise HTTPException(404, "درس یافت نشد")
    return CourseOut.from_model(course)


@router.get("/courses/{course_id}/detail")
async def course_detail(request: Request, course_id: str) -> dict:
    r = _repos(request)
    course = r["courses"].get_by_id(course_id)
    if not course:
        raise HTTPException(404, "درس یافت نشد")
    return {
        "course": CourseOut.from_model(course),
        "contents": [ContentOut.from_model(c) for c in r["contents"].get_by_course(course_id)],
        "events": [EventOut.from_model(e) for e in r["events"].get_by_course(course_id)],
        "posts": [PostOut.from_model(p) for p in r["posts"].get_by_course(course_id)],
        "assignments": [
            AssignmentOut.from_model(a) for a in r["assignments"].get_by_course(course_id)
        ],
        "members": [MemberOut.from_model(m) for m in r["members"].get_by_course(course_id)],
        "changes": [ChangeOut.from_model(c) for c in r["changes"].get_by_course(course_id)],
    }


# === Contents ===


@router.get("/contents", response_model=list[ContentOut])
async def list_contents(request: Request, new_only: bool = False) -> list[ContentOut]:
    repo = ContentRepository(request.app.state.db)
    items = repo.get_new() if new_only else repo.get_all()
    return [ContentOut.from_model(c) for c in items]


# === Events ===


@router.get("/events", response_model=list[EventOut])
async def list_events(request: Request, upcoming: bool = False) -> list[EventOut]:
    repo = EventRepository(request.app.state.db)
    items = repo.get_upcoming(limit=100) if upcoming else repo.get_all()
    return [EventOut.from_model(e) for e in items]


# === Posts ===


@router.get("/posts", response_model=list[PostOut])
async def list_posts(request: Request, new_only: bool = False) -> list[PostOut]:
    repo = PostRepository(request.app.state.db)
    items = repo.get_new() if new_only else repo.get_all()
    return [PostOut.from_model(p) for p in items]


# === Assignments ===


@router.get("/assignments", response_model=list[AssignmentOut])
async def list_assignments(request: Request, new_only: bool = False) -> list[AssignmentOut]:
    repo = AssignmentRepository(request.app.state.db)
    items = repo.get_new() if new_only else repo.get_all()
    return [AssignmentOut.from_model(a) for a in items]


@router.post("/assignments/{assignment_id}/done")
async def set_assignment_done(request: Request, assignment_id: str, done: bool = True) -> dict:
    repo = AssignmentRepository(request.app.state.db)
    if not repo.exists(assignment_id):
        raise HTTPException(404, "تکلیف یافت نشد")
    repo.set_done(assignment_id, done)
    return {"ok": True}


# === Changes ===


@router.get("/changes", response_model=list[ChangeOut])
async def list_changes(request: Request, limit: int = 100) -> list[ChangeOut]:
    repo = ChangeRepository(request.app.state.db)
    return [ChangeOut.from_model(c) for c in repo.get_all(limit=limit)]
