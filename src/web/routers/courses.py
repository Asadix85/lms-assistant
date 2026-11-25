"""Router داده‌های LMS: درس‌ها، محتوا، رویدادها، پست‌ها، تکالیف، اعضا، تغییرات و داشبورد."""

from fastapi import APIRouter, HTTPException, Request
from fastapi import UploadFile, File, Form
import logging

from src.storage.repositories import (
    AssignmentRepository,
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
    QueraCourseRepository,
)
from loguru import logger
from src.storage.repositories.course_schedule_repo import CourseScheduleRepository
from src.models.locations import get_location

from src.web.schemas import (
    AssignmentOut,
    ChangeOut,
    ContentOut,
    CourseOut,
    EventOut,
    SessionOut,
    MemberOut,
    PostOut,
)
from src.web.static_export import build_dashboard

router = APIRouter()


def _require_user(request: Request) -> dict:
    from src.storage.repositories.user_repo import UserRepository
    from src.web.security import SESSION_COOKIE_NAME

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "ابتدا وارد شوید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise HTTPException(401, "نشست منقضی شده است")
    return user


def _repos(request: Request, user_id: str):
    db = request.app.state.db
    return {
        "courses": CourseRepository(db, user_id),
        "contents": ContentRepository(db, user_id),
        "events": EventRepository(db, user_id),
        "posts": PostRepository(db, user_id),
        "assignments": AssignmentRepository(db, user_id),
        "members": MemberRepository(db, user_id),
        "changes": ChangeRepository(db, user_id),
    }


# === Dashboard ===


@router.get("/dashboard")
async def dashboard(request: Request) -> dict:
    user = _require_user(request)
    return build_dashboard(request.app.state.db, user["id"])


# === Courses ===


@router.get("/courses")
async def list_courses(request: Request, active_only: bool = False) -> list[dict]:
    """لیست تمام دروس LMS و کوئرا برای نمایش در فرانت‌اند."""
    db = request.app.state.db

    # ۱. دریافت دروس LMS
    user = _require_user(request)
    course_repo = CourseRepository(db, user["id"])
    lms_courses = course_repo.get_active() if active_only else course_repo.get_all()

    result = []
    for c in lms_courses:
        result.append({
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "group_id": c.group_id,
            "domain": c.domain,
            "teacher": c.teacher or "",
            "code": c.code or "",
            "term": c.term or "",
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "is_new": getattr(c, "is_new", False),
            "source": "lms", # 👈 منبع درس
        })

    # ۲. دریافت کلاس‌های کوئرا
    try:
        quera_repo = QueraCourseRepository(db, user["id"])
        quera_courses = quera_repo.get_all()
        for q in quera_courses:
            if active_only and not q.is_active:
                continue

            # 👇 اگر url خالی بود، یک آدرس پیش‌فرض بساز
            quera_url = q.url if q.url else f"https://quera.org/course/{q.id}"

            result.append({
                "id": q.synthetic_id,
                "name": q.name,
                "url": quera_url,  # 👈 استفاده از آدرس اصلاح‌شده
                "group_id": q.id,
                "domain": "quera",
                "teacher": q.teacher or "کوئرا",
                "code": "",
                "term": "",
                "status": "active" if q.is_active else "finished",
                "is_new": False,
                "source": "quera",
            })
    except Exception as e:
        logger.warning(f"خطا در دریافت دروس کوئرا: {e}")

    return result

@router.get("/courses/overview")
async def courses_overview(request: Request, active_only: bool = False) -> dict:
    """لیست درس‌ها + شمارنده‌ها، با یک‌بار خواندن هر ریپو (بدون N+1)."""
    user = _require_user(request)
    db = request.app.state.db
    uid = user["id"]

    course_repo = CourseRepository(db, uid)
    courses = course_repo.get_active() if active_only else course_repo.get_all()
    assigns = AssignmentRepository(db, uid).get_all()
    contents = ContentRepository(db, uid).get_all()
    posts = PostRepository(db, uid).get_all()
    events = EventRepository(db, uid).get_all()

    stats: dict[str, dict] = {}

    def bucket(cid):
        return stats.setdefault(cid or "", {
            "open": 0, "overdue": 0, "contents": 0, "posts": 0, "events": 0, "last": None,
        })

    for a in assigns:
        b = bucket(a.course_id)
        if not getattr(a, "is_done", False):
            b["open"] += 1
            if getattr(a, "is_expired", False):
                b["overdue"] += 1
    for c in contents:
        bucket(c.course_id)["contents"] += 1
    for p in posts:
        if getattr(p, "is_new", False):
            bucket(p.course_id)["posts"] += 1
    for e in events:
        bucket(e.course_id)["events"] += 1

    for coll in (assigns, contents, posts, events):
        for it in coll:
            ts = getattr(it, "last_seen_at", None) or getattr(it, "first_seen_at", None)
            if not ts:
                continue
            iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            b = bucket(getattr(it, "course_id", None))
            if not b["last"] or iso > b["last"]:
                b["last"] = iso

    empty = {"open": 0, "overdue": 0, "contents": 0, "posts": 0, "events": 0, "last": None}
    result = []
    for c in courses:
        b = stats.get(c.id, empty)
        result.append({
            "id": c.id, "name": c.name, "url": c.url, "group_id": c.group_id,
            "domain": c.domain, "teacher": c.teacher or "", "code": c.code or "",
            "term": c.term or "",
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "is_new": getattr(c, "is_new", False), "source": "lms",
            "stats": {k: v for k, v in b.items() if k != "last"},
            "last_activity": b["last"],
        })

    try:
        qstats: dict[str, dict] = {}
        from src.storage.repositories import QueraAssignmentRepository
        for qa in QueraAssignmentRepository(db, uid).get_all():
            b = qstats.setdefault(qa.course_name, {"open": 0, "overdue": 0})
            if not qa.is_done:
                b["open"] += 1
                if qa.is_expired:
                    b["overdue"] += 1
        for q in QueraCourseRepository(db, uid).get_all():
            if active_only and not q.is_active:
                continue
            b = qstats.get(q.name, {"open": 0, "overdue": 0})
            result.append({
                "id": q.synthetic_id, "name": q.name,
                "url": q.url or f"https://quera.org/course/{q.id}",
                "group_id": q.id, "domain": "quera", "teacher": q.teacher or "کوئرا",
                "code": "", "term": "",
                "status": "active" if q.is_active else "finished",
                "is_new": False, "source": "quera",
                "stats": {**empty, **b}, "last_activity": None,
            })
    except Exception as e:
        logger.warning(f"خطا در overview کوئرا: {e}")

    return {"ok": True, "courses": result}

@router.get("/courses/{course_id}", response_model=CourseOut)
async def get_course(request: Request, course_id: str) -> CourseOut:
    user = _require_user(request)
    repo = CourseRepository(request.app.state.db, user["id"])
    course = repo.get_by_id(course_id)
    if not course:
        raise HTTPException(404, "درس یافت نشد")
    return CourseOut.from_model(course)


@router.get("/courses/{course_id}/detail")
async def course_detail(request: Request, course_id: str) -> dict:
    user = _require_user(request)
    r = _repos(request, user["id"])
    course = r["courses"].get_by_id(course_id)
    if not course:
        raise HTTPException(404, "درس یافت نشد")

    locations_data = []
    schedule_repo = CourseScheduleRepository(request.app.state.db, user["id"])
    schedule = schedule_repo.get_by_id(course_id) or schedule_repo.get_by_id(course.group_id)

    if schedule and schedule.sessions:
        for session in schedule.sessions:
            loc_info = get_location(session.location)
            if loc_info:
                locations_data.append(
                    SessionOut(
                        weekday=session.weekday,
                        start_time=session.start_time,
                        end_time=session.end_time,
                        location_text=session.location,
                        faculty=loc_info.name,
                        building=loc_info.building,
                        lat=loc_info.lat,
                        lng=loc_info.lng,
                    )
                )
            elif session.location:
                locations_data.append(
                    SessionOut(
                        weekday=session.weekday,
                        start_time=session.start_time,
                        end_time=session.end_time,
                        location_text=session.location,
                        faculty="مکان ثبت شده در LMS",
                        building=session.location,
                        lat=32.6072163,  # مرکز دانشگاه اصفهان
                        lng=51.6583164,
                    )
                )

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
        "locations": locations_data,
    }

# === Contents ===


@router.get("/contents", response_model=list[dict])
async def list_contents(request: Request, new_only: bool = False) -> list[dict]:
    db = request.app.state.db
    user = _require_user(request)
    repo = ContentRepository(db, user["id"])
    items = repo.get_new() if new_only else repo.get_all()

    # دریافت لیست دروس برای تطبیق نام و استاد
    course_repo = CourseRepository(db, user["id"])
    courses = course_repo.get_all()
    course_map = {c.id: c for c in courses}

    result = []
    for c in items:
        course = course_map.get(c.course_id)
        result.append({
            "id": c.id,
            "course_id": c.course_id,
            "course_name": course.name if course else "درس نامشخص",
            "teacher": course.teacher.replace("استاد ", "").strip() if course and course.teacher else "سیستم",
            "title": c.title,
            "url": c.url,
            "content_type": c.content_type,
            "filename": c.filename,
            "last_seen_at": c.first_seen_at.isoformat() if hasattr(c, "first_seen_at") and c.first_seen_at else None,
        })
    return result

# === Events ===

@router.get("/events")
async def list_events(request: Request, upcoming: bool = False) -> list[dict]:
    db = request.app.state.db
    user = _require_user(request)
    repo = EventRepository(db, user["id"])
    items = repo.get_upcoming(limit=100) if upcoming else repo.get_all()

    # دریافت لیست دروس برای پیدا کردن نام
    course_repo = CourseRepository(db, user["id"])
    courses = course_repo.get_all()
    course_map = {c.id: c.name for c in courses}

    result = []
    for e in items:
        evt_type = e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type)

        # 👇 پیدا کردن نام درس
        course_name = "عمومی"
        if e.course_id and e.course_id in course_map:
            course_name = course_map[e.course_id]

        result.append({
            "id": e.id,
            "title": e.title,
            "event_type": evt_type,
            "url": e.url,
            "start_at": e.start_at.isoformat() if e.start_at else None,
            "end_at": e.end_at.isoformat() if e.end_at else None,
            "description": e.description,
            "course_id": e.course_id,
            "course_name": course_name,
            "is_new": getattr(e, "is_new", False),
            "is_manual": str(e.id).startswith("manual_"),
        })
    return result


from pydantic import BaseModel
from datetime import datetime


class ManualEventSchema(BaseModel):
    title: str
    description: str = ""
    date: str  # فرمت YYYY-MM-DD
    time: str  # فرمت HH:MM
    event_type: str = "assignment"  # یا "exam"
    course_id: str | None = None


@router.post("/events/manual")
async def add_manual_event(request: Request, body: ManualEventSchema):
    db = request.app.state.db
    user = _require_user(request)
    event_repo = EventRepository(db, user["id"])

    from uuid import uuid4
    event_id = f"manual_{int(datetime.now().timestamp())}_{uuid4().hex[:6]}"

    try:
        dt_str = f"{body.date} {body.time}:00"
        start_at = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "فرمت تاریخ یا ساعت نامعتبر است")

    from src.models.event import Event, EventType

    evt_type = EventType.ASSIGNMENT if body.event_type == "assignment" else EventType.EXAM

    event = Event(
        id=event_id,
        title=body.title,
        description=body.description,
        event_type=evt_type,
        start_at=start_at,
        end_at=None,
        url=None,
        course_id=body.course_id,  # 👈 ذخیره در دیتابیس
        is_new=True
    )

    event_repo.save(event)

    return {"ok": True, "id": event_id}
class ManualEventUpdateSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    date: str | None = None
    time: str | None = None
    event_type: str | None = None
    course_id: str | None = None
    clear_course: bool = False


def _manual_event_or_404(repo: EventRepository, event_id: str):
    if not str(event_id).startswith("manual_"):
        raise HTTPException(400, "فقط رویدادهای دستی قابل ویرایش یا حذف هستند")

    event = repo.get_by_id(event_id)
    if not event:
        raise HTTPException(404, "رویداد یافت نشد")

    return event


@router.patch("/events/{event_id}")
async def update_manual_event(
    request: Request,
    event_id: str,
    body: ManualEventUpdateSchema,
):
    user = _require_user(request)
    repo = EventRepository(request.app.state.db, user["id"])
    event = _manual_event_or_404(repo, event_id)

    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(400, "عنوان نمی‌تواند خالی باشد")
        event.title = title

    if body.description is not None:
        event.description = body.description

    if body.event_type is not None:
        if body.event_type not in ("assignment", "exam"):
            raise HTTPException(400, "نوع رویداد فقط assignment یا exam است")

        from src.models.event import EventType

        event.event_type = (
            EventType.ASSIGNMENT
            if body.event_type == "assignment"
            else EventType.EXAM
        )

    if body.clear_course:
        event.course_id = None
    elif body.course_id is not None:
        event.course_id = body.course_id or None

    if body.date or body.time:
        cur = event.start_at or datetime.now()
        date_s = body.date or cur.strftime("%Y-%m-%d")
        time_s = body.time or cur.strftime("%H:%M")

        try:
            event.start_at = datetime.strptime(
                f"{date_s} {time_s}:00",
                "%Y-%m-%d %H:%M:%S",
            )
        except ValueError:
            raise HTTPException(400, "فرمت تاریخ یا ساعت نامعتبر است")

    event.last_seen_at = datetime.now()

    repo.update_manual(event)
    return {"ok": True, "id": event_id}


@router.delete("/events/{event_id}")
async def delete_manual_event(request: Request, event_id: str):
    user = _require_user(request)
    repo = EventRepository(request.app.state.db, user["id"])

    _manual_event_or_404(repo, event_id)

    if not repo.delete(event_id):
        raise HTTPException(404, "رویداد یافت نشد")

    return {"ok": True, "id": event_id}

# === Posts ===


@router.get("/posts", response_model=list[PostOut])
async def list_posts(request: Request, new_only: bool = False) -> list[PostOut]:
    user = _require_user(request)
    repo = PostRepository(request.app.state.db, user["id"])
    items = repo.get_new() if new_only else repo.get_all()
    return [PostOut.from_model(p) for p in items]


@router.post("/posts/read")
async def mark_posts_read(request: Request) -> dict:
    """علامت‌گذاری همه پست‌ها به‌عنوان خوانده‌شده (is_new = 0)."""
    user = _require_user(request)
    repo = PostRepository(request.app.state.db, user["id"])
    repo.mark_all_seen()
    return {"ok": True}


# === Assignments ===


@router.get("/assignments")
async def list_assignments(request: Request, new_only: bool = False) -> list[dict]:
    db = request.app.state.db
    user = _require_user(request)
    repo = AssignmentRepository(db, user["id"])
    items = repo.get_new() if new_only else repo.get_all()

    course_repo = CourseRepository(db, user["id"])
    courses = course_repo.get_all()
    course_map = {c.id: c.name for c in courses}

    result = []
    for a in items:
        course_name = course_map.get(a.course_id, "درس نامشخص") if a.course_id else "درس نامشخص"

        result.append({
            "id": a.id,
            "course_id": a.course_id,
            "course_name": course_name,
            "title": a.title,
            "description": a.description,
            "start_at": a.start_at.isoformat() if a.start_at else None,
            "deadline": a.deadline.isoformat() if a.deadline else None,
            "deadline_jalali": a.deadline_jalali,
            "submit_url": a.submit_url,
            "view_url": a.view_url,
            "response_count": a.response_count,
            "is_new": getattr(a, "is_new", False),
            "is_manual": getattr(a, "is_manual", False),
            "is_done": getattr(a, "is_done", False),
            "is_expired": getattr(a, "is_expired", False),
            "source": "lms", # 👈 منبع
        })

    # 👇 اضافه کردن تکالیف کوئرا
    try:
        from src.storage.repositories import QueraAssignmentRepository
        quera_repo = QueraAssignmentRepository(db, user["id"])
        quera_assignments = quera_repo.get_all()

        for qa in quera_assignments:
            result.append({
                "id": f"quera_{qa.id}",
                "course_id": f"quera_{qa.course_name}",
                "course_name": f"کوئرا - {qa.course_name}",
                "title": qa.name,
                "description": "",
                "start_at": None,
                "deadline": qa.finish_time.isoformat() if qa.finish_time else None,
                "deadline_jalali": None,
                "submit_url": None,
                "view_url": None,
                "response_count": qa.submitted_count,
                "is_new": False,
                "is_manual": False,
                "is_done": qa.is_done,
                "is_expired": qa.is_expired,
                "source": "quera", # 👈 منبع
            })
    except Exception as e:
        logger.warning(f"خطا در دریافت تکالیف کوئرا: {e}")

    return result


@router.post("/assignments/{assignment_id}/done")
async def set_assignment_done(request: Request, assignment_id: str, done: bool = True) -> dict:
    user = _require_user(request)
    repo = AssignmentRepository(request.app.state.db, user["id"])
    if not repo.exists(assignment_id):
        raise HTTPException(404, "تکلیف یافت نشد")
    repo.set_done(assignment_id, done)
    return {"ok": True}

class ManualAssignmentSchema(BaseModel):
    title: str
    course_id: str
    description: str = ""
    date: str          # YYYY-MM-DD
    time: str = "23:59"


class AssignmentUpdateSchema(BaseModel):
    title: str | None = None
    description: str | None = None
    date: str | None = None
    time: str | None = None
    course_id: str | None = None


class BulkDoneBody(BaseModel):
    ids: list[str] = []
    done: bool = True


def _manual_assignment_or_400(repo: AssignmentRepository, aid: str):
    a = repo.get_by_id(aid)
    if not a:
        raise HTTPException(404, "تکلیف یافت نشد")
    if not getattr(a, "is_manual", False):
        raise HTTPException(400, "فقط تکالیف دستی قابل ویرایش یا حذف هستند")
    return a


@router.post("/assignments/manual")
async def add_manual_assignment(request: Request, body: ManualAssignmentSchema):
    user = _require_user(request)
    repo = AssignmentRepository(request.app.state.db, user["id"])

    title = (body.title or "").strip()
    if not title:
        raise HTTPException(400, "عنوان الزامی است")
    if not (body.course_id or "").strip():
        raise HTTPException(400, "انتخاب درس الزامی است")
    try:
        deadline = datetime.strptime(f"{body.date} {body.time}:00", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "فرمت تاریخ یا ساعت نامعتبر است")

    from uuid import uuid4
    from src.models.assignment import Assignment

    now = datetime.now()
    aid = f"manual_{int(now.timestamp())}_{uuid4().hex[:6]}"
    repo.save(Assignment(
        id=aid,
        course_id=body.course_id.strip(),
        title=title,
        description=body.description or "",
        post_id=None,
        start_at=None,
        deadline=deadline,
        start_at_jalali=None,
        deadline_jalali=None,
        submit_url=None,
        view_url=None,
        response_count=0,
        is_new=True,
        is_manual=True,
        is_done=False,
        first_seen_at=now,
        last_seen_at=now,
    ))
    return {"ok": True, "id": aid}


@router.patch("/assignments/{assignment_id}")
async def update_manual_assignment(request: Request, assignment_id: str, body: AssignmentUpdateSchema):
    user = _require_user(request)
    repo = AssignmentRepository(request.app.state.db, user["id"])
    a = _manual_assignment_or_400(repo, assignment_id)

    if body.title is not None:
        t = body.title.strip()
        if not t:
            raise HTTPException(400, "عنوان نمی‌تواند خالی باشد")
        a.title = t
    if body.description is not None:
        a.description = body.description
    if body.course_id is not None and body.course_id.strip():
        a.course_id = body.course_id.strip()
    if body.date or body.time:
        cur = a.deadline or datetime.now()
        date_s = body.date or cur.strftime("%Y-%m-%d")
        time_s = body.time or cur.strftime("%H:%M")
        try:
            a.deadline = datetime.strptime(f"{date_s} {time_s}:00", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(400, "فرمت تاریخ یا ساعت نامعتبر است")
        a.deadline_jalali = None  # فرانت از ISO محاسبه می‌کند

    a.last_seen_at = datetime.now()
    repo.save(a)
    return {"ok": True, "id": assignment_id}


@router.delete("/assignments/{assignment_id}")
async def delete_manual_assignment(request: Request, assignment_id: str):
    user = _require_user(request)
    repo = AssignmentRepository(request.app.state.db, user["id"])
    _manual_assignment_or_400(repo, assignment_id)
    repo.delete(assignment_id)
    return {"ok": True, "id": assignment_id}


@router.post("/assignments/bulk-done")
async def bulk_assignments_done(request: Request, body: BulkDoneBody):
    user = _require_user(request)
    repo = AssignmentRepository(request.app.state.db, user["id"])
    updated, skipped = [], []
    for aid in (body.ids or [])[:200]:
        if str(aid).startswith("quera_") or not repo.get_by_id(aid):
            skipped.append(aid)
            continue
        repo.set_done(aid, body.done)
        updated.append(aid)
    return {"ok": True, "updated": updated, "skipped": skipped}

@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    request: Request,
    assignment_id: str,
    file: UploadFile = File(...),
    description: str = Form("")
):
    """ارسال فایل تکلیف به LMS با استفاده از نشست فعال."""
    from src.storage.repositories.user_repo import UserRepository
    from src.web.security import SESSION_COOKIE_NAME

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "ابتدا لاگین کنید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise HTTPException(401, "نشست منقضی شده است")

    session = request.app.state.session
    session.set_active_user(user["id"])
    try:
        assistant = session.get_assistant(user["id"])
    except PermissionError as e:
        raise HTTPException(401, f"ابتدا لاگین کنید: {e}")

    if not assistant or not assistant.is_authenticated:
        raise HTTPException(401, "ابتدا لاگین کنید")

    try:
        # ۱. پیدا کردن URL ارسال تکلیف از دیتابیس
        db = request.app.state.db
        assignment_repo = AssignmentRepository(db, user["id"])
        assignment = assignment_repo.get_by_id(assignment_id)

        if not assignment or not assignment.submit_url:
            raise HTTPException(404, "آدرس ارسال تکلیف یافت نشد")

        # ۲. خواندن محتوای فایل
        file_content = await file.read()

        # ۳. ارسال فایل با httpx
        # ⚠️ ساختار دقیق این درخواست بستگی به فرم LMS دارد
        files = {'file': (file.filename, file_content, file.content_type)}
        data = {'description': description}

        response = assistant.client.post(
            assignment.submit_url,
            files=files,
            data=data
        )

        if response.status_code in (200, 302):
            return {"ok": True, "message": "تکلیف با موفقیت ارسال شد."}
        else:
            return {"ok": False, "error": f"خطا در ارسال: {response.status_code}"}

    except Exception as e:
        logger.error(f"خطا در ارسال تکلیف: {e}")
        raise HTTPException(500, str(e))


# === Changes ===


@router.get("/changes")
async def list_changes(request: Request, limit: int = 100) -> list[dict]:
    db = request.app.state.db
    user = _require_user(request)
    repo = ChangeRepository(db, user["id"])
    changes = repo.get_all(limit=limit)

    course_repo = CourseRepository(db, user["id"])
    courses = course_repo.get_all()
    course_map = {c.id: c for c in courses}

    result = []
    for ch in changes:
        course = course_map.get(ch.course_id)
        course_name = course.name if course else "عمومی"
        teacher_name = course.teacher.replace("استاد ", "").strip() if course and course.teacher else "سیستم"

        entity_type = ch.entity_type.value if hasattr(ch.entity_type, "value") else str(ch.entity_type)

        # 👇 استخراج عنوان از دیتای تغییر (که در زمان سینک ذخیره شده)
        data = ch.data or {}
        title = (
                data.get("title") or
                data.get("name") or
                data.get("text") or
                data.get("filename") or
                ""
        )

        # اگر عنوان خالی بود، یک عنوان پیش‌فرض بر اساس نوع موجودیت بساز
        if not title:
            title = f"{entity_type} جدید"
            if entity_type == "content":
                title = "فایل/محتوا جدید"
            elif entity_type == "event":
                title = "رویداد جدید"
            elif entity_type == "assignment":
                title = "تکلیف جدید"
            elif entity_type == "post":
                title = "پیام جدید"

        # اگر نام استاد در دیتا بود، آن را اولویت بده
        if data.get("author"):
            teacher_name = data.get("author")
        elif data.get("teacher"):
            teacher_name = data.get("teacher")

        result.append({
            "id": str(getattr(ch, "id", hash(ch.detected_at))),
            "type": ch.type.value if hasattr(ch.type, "value") else str(ch.type),
            "entity_type": entity_type,
            "course_id": ch.course_id,
            "course_name": course_name,
            "teacher_name": teacher_name,
            "title": str(title),
            "detected_at": ch.detected_at.isoformat() if ch.detected_at else None,
        })
    return result


@router.get("/map/locations")
async def get_all_locations(request: Request) -> list[dict]:
    """استخراج تمام مکان‌های منحصر به فرد از کلاس‌های فعال برای نمایش روی نقشه."""
    db = request.app.state.db
    user = _require_user(request)
    course_repo = CourseRepository(db, user["id"])
    schedule_repo = CourseScheduleRepository(db, user["id"])

    courses = course_repo.get_active()  # فقط دروس فعال
    unique_locations = {}

    for c in courses:
        schedule = schedule_repo.get_by_id(c.group_id)
        if schedule and schedule.sessions:
            for session in schedule.sessions:
                if session.location:
                    loc_info = get_location(session.location)
                    if loc_info:
                        # اگر قبلاً اضافه نشده، اضافه کن
                        if loc_info.name not in unique_locations:
                            unique_locations[loc_info.name] = {
                                "name": loc_info.name,
                                "building": loc_info.building,
                                "lat": loc_info.lat,
                                "lng": loc_info.lng,
                                "courses": [c.name]  # لیست دروسی که در این مکان برگزار می‌شوند
                            }
                        else:
                            # اگر قبلاً بود، نام درس را به لیست اضافه کن (بدون تکرار)
                            if c.name not in unique_locations[loc_info.name]["courses"]:
                                unique_locations[loc_info.name]["courses"].append(c.name)

    return list(unique_locations.values())


@router.get("/calendar.ics")
async def export_calendar_ics(request: Request):
    """دانلود تقویم ICS شامل تکالیف (با مهلت) و رویدادها."""
    from fastapi.responses import Response
    from src.web.ics_export import build_ics

    user = _require_user(request)
    r = _repos(request, user["id"])
    assignments = [a for a in r["assignments"].get_all() if getattr(a, "deadline", None)]
    events = r["events"].get_all()
    name = f"LMS - {user.get('full_name') or user.get('lms_username') or 'me'}"
    body = build_ics(assignments=assignments, events=events, calendar_name=name)
    return Response(
        content=body,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="lms-assistant.ics"',
            "Cache-Control": "no-store",
        },
    )

# =========================================================================
# کاتالوگ مکان‌های دانشگاه — ایستگاه اتوبوس، سلف، کتابخانه و …
# ذخیره در data/places.json (بدون نیاز به migration دیتابیس)
# =========================================================================
import json
from pathlib import Path

MAP_CATEGORIES = [
    {"id": "class",   "title": "کلاس و دانشکده",   "icon": "🏛"},
    {"id": "bus",     "title": "ایستگاه اتوبوس",    "icon": "🚌"},
    {"id": "food",    "title": "تغذیه و سلف",       "icon": "🍽"},
    {"id": "study",   "title": "کتابخانه و مطالعه", "icon": "📚"},
    {"id": "dorm",    "title": "خوابگاه",           "icon": "🛏"},
    {"id": "sport",   "title": "ورزشی",             "icon": "🏅"},
    {"id": "health",  "title": "درمانی",            "icon": "🩺"},
    {"id": "service", "title": "خدمات اداری",       "icon": "🏢"},
    {"id": "gate",    "title": "درها و ورودی",      "icon": "🚪"},
    {"id": "parking", "title": "پارکینگ",           "icon": "🅿️"},
]

# مختصات‌ها نمونهٔ اولیه‌اند؛ ادمین از خود نقشه اصلاحشان می‌کند.
SEED_PLACES = [
    {"id": "p_gate_main", "cat": "gate", "name": "در اصلی دانشگاه", "lat": 32.6110, "lng": 51.6560,
     "desc": "ورودی اصلی و نگهبانی مرکزی؛ دسترسی به تاکسی و اتوبوس شهری.", "hours": "۲۴ ساعته", "tags": ["نگهبانی", "ورودی"]},
    {"id": "p_gate_east", "cat": "gate", "name": "در شرقی", "lat": 32.6075, "lng": 51.6640,
     "desc": "ورودی سمت دانشکده‌های فنی و مهندسی.", "hours": "۶ تا ۲۲", "tags": ["ورودی"]},
    {"id": "p_bus_main", "cat": "bus", "name": "ایستگاه اتوبوس — در اصلی", "lat": 32.6108, "lng": 51.6555,
     "desc": "ایستگاه اصلی سرویس داخل دانشگاه و خطوط شهری.", "hours": "۶:۳۰ تا ۲۱", "tags": ["سرویس", "شهری"],
     "lines": ["سرویس در اصلی ↔ خوابگاه", "سرویس در اصلی ↔ دانشکده فنی"]},
    {"id": "p_bus_eng", "cat": "bus", "name": "ایستگاه اتوبوس — دانشکده فنی", "lat": 32.6065, "lng": 51.6600,
     "desc": "نزدیک‌ترین ایستگاه به دانشکده‌های مهندسی.", "hours": "۶:۳۰ تا ۲۱", "tags": ["سرویس"],
     "lines": ["سرویس فنی ↔ در اصلی"]},
    {"id": "p_bus_dorm", "cat": "bus", "name": "ایستگاه اتوبوس — خوابگاه", "lat": 32.6030, "lng": 51.6555,
     "desc": "سرویس رفت‌وبرگشت خوابگاه برادران.", "hours": "۶:۳۰ تا ۲۲", "tags": ["سرویس", "خوابگاه"],
     "lines": ["سرویس خوابگاه ↔ در اصلی"]},
    {"id": "p_bus_lib", "cat": "bus", "name": "ایستگاه اتوبوس — کتابخانه مرکزی", "lat": 32.6080, "lng": 51.6585,
     "desc": "ایستگاه میانی، نزدیک کتابخانه و آموزش کل.", "hours": "۶:۳۰ تا ۲۱", "tags": ["سرویس"],
     "lines": ["سرویس مرکزی"]},
    {"id": "p_lib", "cat": "study", "name": "کتابخانه مرکزی", "lat": 32.6082, "lng": 51.6588,
     "desc": "منابع، سالن مطالعه و بخش مرجع.", "hours": "شنبه تا چهارشنبه ۷:۳۰–۱۹", "tags": ["مطالعه", "امانت"]},
    {"id": "p_study_hall", "cat": "study", "name": "سالن مطالعه شبانه‌روزی", "lat": 32.6079, "lng": 51.6592,
     "desc": "فضای مطالعه ساکت با پریز برق و وای‌فای.", "hours": "۲۴ ساعته", "tags": ["ساکت", "وای‌فای"]},
    {"id": "p_food_main", "cat": "food", "name": "سلف مرکزی", "lat": 32.6055, "lng": 51.6570,
     "desc": "رزرو غذا از سامانه تغذیه؛ پرداخت با کارت دانشجویی.", "hours": "۱۱:۳۰ تا ۱۴:۳۰", "tags": ["رزرو", "کارت تغذیه"]},
    {"id": "p_food_eng", "cat": "food", "name": "بوفه دانشکده فنی", "lat": 32.6062, "lng": 51.6605,
     "desc": "میان‌وعده، نوشیدنی گرم و ساندویچ.", "hours": "۸ تا ۱۶", "tags": ["بوفه"]},
    {"id": "p_ce", "cat": "class", "name": "دانشکده مهندسی کامپیوتر", "lat": 32.6060, "lng": 51.6608,
     "desc": "کلاس‌های کارشناسی و ارشد، سایت و آزمایشگاه‌ها.", "hours": "۷ تا ۲۰", "tags": ["کلاس", "سایت"]},
    {"id": "p_sci", "cat": "class", "name": "دانشکده علوم", "lat": 32.6090, "lng": 51.6600,
     "desc": "ریاضی، فیزیک، شیمی و زیست.", "hours": "۷ تا ۲۰", "tags": ["کلاس"]},
    {"id": "p_lit", "cat": "class", "name": "دانشکده ادبیات و علوم انسانی", "lat": 32.6095, "lng": 51.6565,
     "desc": "کلاس‌های علوم انسانی و زبان.", "hours": "۷ تا ۲۰", "tags": ["کلاس"]},
    {"id": "p_health", "cat": "health", "name": "مرکز بهداشت و درمان", "lat": 32.6045, "lng": 51.6580,
     "desc": "ویزیت عمومی، اورژانس سبک و مشاوره سلامت.", "hours": "۸ تا ۱۶", "tags": ["پزشک", "اورژانس"]},
    {"id": "p_gym", "cat": "sport", "name": "سالن ورزشی", "lat": 32.6025, "lng": 51.6595,
     "desc": "فوتسال، بسکتبال و بدنسازی.", "hours": "۸ تا ۲۱", "tags": ["رزرو"]},
    {"id": "p_pool", "cat": "sport", "name": "استخر", "lat": 32.6020, "lng": 51.6600,
     "desc": "سانس‌های جداگانه؛ بلیت از سامانه تربیت بدنی.", "hours": "سانس‌بندی", "tags": ["بلیت"]},
    {"id": "p_dorm_m", "cat": "dorm", "name": "خوابگاه برادران", "lat": 32.6015, "lng": 51.6550,
     "desc": "بلوک‌های الف تا د، سالن مطالعه و اینترنت.", "hours": "۲۴ ساعته", "tags": ["سکونت"]},
    {"id": "p_dorm_f", "cat": "dorm", "name": "خوابگاه خواهران", "lat": 32.6120, "lng": 51.6590,
     "desc": "ورودی مجزا، نگهبانی شبانه‌روزی.", "hours": "۲۴ ساعته", "tags": ["سکونت"]},
    {"id": "p_parking", "cat": "parking", "name": "پارکینگ مرکزی", "lat": 32.6100, "lng": 51.6570,
     "desc": "ظرفیت محدود؛ ورود با کارت شناسایی.", "hours": "۶ تا ۲۲", "tags": ["خودرو"]},
    {"id": "p_edu", "cat": "service", "name": "آموزش کل", "lat": 32.6085, "lng": 51.6570,
     "desc": "امور فارغ‌التحصیلی، انتخاب واحد و گواهی اشتغال.", "hours": "۷:۳۰ تا ۱۴", "tags": ["اداری"]},
    {"id": "p_student", "cat": "service", "name": "امور دانشجویی", "lat": 32.6087, "lng": 51.6567,
     "desc": "وام، خوابگاه، تغذیه و مشاوره.", "hours": "۷:۳۰ تا ۱۴", "tags": ["اداری"]},
    {"id": "p_mosque", "cat": "service", "name": "مسجد دانشگاه", "lat": 32.6068, "lng": 51.6575,
     "desc": "نماز جماعت و برنامه‌های فرهنگی.", "hours": "اذان تا ۲۱", "tags": ["فرهنگی"]},
]


class PlaceBody(BaseModel):
    name: str
    cat: str
    lat: float
    lng: float
    desc: str = ""
    hours: str = ""
    tags: list[str] = []
    lines: list[str] = []


class PlaceUpdateBody(BaseModel):
    name: str | None = None
    cat: str | None = None
    lat: float | None = None
    lng: float | None = None
    desc: str | None = None
    hours: str | None = None
    tags: list[str] | None = None
    lines: list[str] | None = None


def _places_file() -> Path:
    from config.settings import settings
    return Path(settings.db_path).parent / "places.json"


def _places_load() -> list[dict]:
    f = _places_file()
    if f.exists():
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(rows, list):
                return rows
        except Exception as e:
            logger.warning(f"places.json خوانده نشد: {e}")
    return [dict(p) for p in SEED_PLACES]


def _places_save(rows: list[dict]) -> None:
    f = _places_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def _valid_cat(cat: str) -> bool:
    return cat in {c["id"] for c in MAP_CATEGORIES}


@router.get("/map/places")
async def list_places(request: Request) -> dict:
    _require_user(request)
    return {"ok": True, "categories": MAP_CATEGORIES, "places": _places_load()}


@router.post("/map/places")
async def add_place(request: Request, body: PlaceBody):
    from src.web.deps import require_admin
    require_admin(request)
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(400, "نام مکان الزامی است")
    if not _valid_cat(body.cat):
        raise HTTPException(400, "دستهٔ نامعتبر")
    if not (-90 <= body.lat <= 90 and -180 <= body.lng <= 180):
        raise HTTPException(400, "مختصات نامعتبر")

    from uuid import uuid4
    rows = _places_load()
    pid = f"p_{uuid4().hex[:10]}"
    rows.append({
        "id": pid, "cat": body.cat, "name": name,
        "lat": round(body.lat, 6), "lng": round(body.lng, 6),
        "desc": body.desc or "", "hours": body.hours or "",
        "tags": body.tags or [], "lines": body.lines or [],
    })
    _places_save(rows)
    return {"ok": True, "id": pid}


@router.patch("/map/places/{place_id}")
async def update_place(request: Request, place_id: str, body: PlaceUpdateBody):
    from src.web.deps import require_admin
    require_admin(request)
    rows = _places_load()
    row = next((r for r in rows if r.get("id") == place_id), None)
    if not row:
        raise HTTPException(404, "مکان یافت نشد")

    if body.name is not None:
        n = body.name.strip()
        if not n:
            raise HTTPException(400, "نام نمی‌تواند خالی باشد")
        row["name"] = n
    if body.cat is not None:
        if not _valid_cat(body.cat):
            raise HTTPException(400, "دستهٔ نامعتبر")
        row["cat"] = body.cat
    if body.lat is not None:
        if not -90 <= body.lat <= 90:
            raise HTTPException(400, "عرض جغرافیایی نامعتبر")
        row["lat"] = round(body.lat, 6)
    if body.lng is not None:
        if not -180 <= body.lng <= 180:
            raise HTTPException(400, "طول جغرافیایی نامعتبر")
        row["lng"] = round(body.lng, 6)
    for k in ("desc", "hours", "tags", "lines"):
        v = getattr(body, k)
        if v is not None:
            row[k] = v

    _places_save(rows)
    return {"ok": True, "id": place_id}


@router.delete("/map/places/{place_id}")
async def delete_place(request: Request, place_id: str):
    from src.web.deps import require_admin
    require_admin(request)
    rows = _places_load()
    left = [r for r in rows if r.get("id") != place_id]
    if len(left) == len(rows):
        raise HTTPException(404, "مکان یافت نشد")
    _places_save(left)
    return {"ok": True, "id": place_id}

