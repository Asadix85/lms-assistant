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
    return build_dashboard(request.app.state.db)


# === Courses ===


@router.get("/courses")
async def list_courses(request: Request, active_only: bool = False) -> list[dict]:
    """لیست تمام دروس LMS و کوئرا برای نمایش در فرانت‌اند."""
    db = request.app.state.db

    # ۱. دریافت دروس LMS
    course_repo = CourseRepository(db)
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
        quera_repo = QueraCourseRepository(db)
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

    locations_data = []
    schedule_repo = CourseScheduleRepository(request.app.state.db)
    schedule = schedule_repo.get_by_id(course_id)

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
    repo = ContentRepository(db)
    items = repo.get_new() if new_only else repo.get_all()
    
    # دریافت لیست دروس برای تطبیق نام و استاد
    course_repo = CourseRepository(db)
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
    repo = EventRepository(db)
    items = repo.get_upcoming(limit=100) if upcoming else repo.get_all()

    # دریافت لیست دروس برای پیدا کردن نام
    course_repo = CourseRepository(db)
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
            "course_name": course_name,  # 👈 اضافه شد
            "is_new": getattr(e, "is_new", False),
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
    event_repo = EventRepository(db)

    event_id = f"manual_{int(datetime.now().timestamp())}"

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

# === Posts ===


@router.get("/posts", response_model=list[PostOut])
async def list_posts(request: Request, new_only: bool = False) -> list[PostOut]:
    repo = PostRepository(request.app.state.db)
    items = repo.get_new() if new_only else repo.get_all()
    return [PostOut.from_model(p) for p in items]


@router.post("/posts/read")
async def mark_posts_read(request: Request) -> dict:
    """علامت‌گذاری همه پست‌ها به‌عنوان خوانده‌شده (is_new = 0)."""
    repo = PostRepository(request.app.state.db)
    repo.mark_all_seen()
    return {"ok": True}


# === Assignments ===


@router.get("/assignments")
async def list_assignments(request: Request, new_only: bool = False) -> list[dict]:
    db = request.app.state.db
    repo = AssignmentRepository(db)
    items = repo.get_new() if new_only else repo.get_all()

    course_repo = CourseRepository(db)
    courses = course_repo.get_all()
    course_map = {c.id: c.name for c in courses}

    result = []
    for a in items:
        course_name = course_map.get(a.course_id, "درس نامشخص") if a.course_id else "درس نامشخص"

        result.append({
            "id": a.id,
            "course_id": a.course_id,
            "course_name": course_name,  # 👈 اضافه شد
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
        })
    return result


@router.post("/assignments/{assignment_id}/done")
async def set_assignment_done(request: Request, assignment_id: str, done: bool = True) -> dict:
    repo = AssignmentRepository(request.app.state.db)
    if not repo.exists(assignment_id):
        raise HTTPException(404, "تکلیف یافت نشد")
    repo.set_done(assignment_id, done)
    return {"ok": True}

@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    request: Request,
    assignment_id: str,
    file: UploadFile = File(...),
    description: str = Form("")
):
    """ارسال فایل تکلیف به LMS با استفاده از نشست فعال."""
    # 👇 گرفتن assistant از SessionManager
    session = request.app.state.session
    try:
        assistant = session.get_assistant()
    except PermissionError as e:
        raise HTTPException(401, f"ابتدا لاگین کنید: {e}")
    
    if not assistant or not assistant.is_authenticated:
        raise HTTPException(401, "ابتدا لاگین کنید")

    try:
        # ۱. پیدا کردن URL ارسال تکلیف از دیتابیس
        db = request.app.state.db
        assignment_repo = AssignmentRepository(db)
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
    repo = ChangeRepository(db)
    changes = repo.get_all(limit=limit)

    course_repo = CourseRepository(db)
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
    course_repo = CourseRepository(db)
    schedule_repo = CourseScheduleRepository(db)

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
