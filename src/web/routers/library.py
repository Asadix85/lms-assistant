"""API کتابخانه عمومی: لیست درس‌ها، ارسال لینک، امتیاز، نظر، گزارش و تایید ادمین."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.storage.repositories.library_repo import LibraryRepository
from src.storage.repositories.setting_repo import SettingRepository
from src.web.deps import get_current_user, require_admin

router = APIRouter()

LIBRARY_TERMS_VERSION = "1"
LIBRARY_TERMS_TEXT = (
    "با ارسال منبع در کتابخانه موافقت می‌کنید که:\n"
    "۱) لینک متعلق به خودتان است یا اجازهٔ اشتراک آن را دارید.\n"
    "۲) محتوا توهین‌آمیز، غیراخلاقی یا ناقض حقوق دیگران نیست.\n"
    "۳) لینک‌های شکسته، اسپم یا تبلیغاتی ارسال نمی‌کنید.\n"
    "۴) ادمین می‌تواند منبع را رد، حذف یا ویرایش کند.\n"
    "۵) مسئولیت صحت محتوا با ارسال‌کننده است."
)
TERMS_SETTING_KEY = "library_terms_accepted_v1"


def _repo(request: Request) -> LibraryRepository:
    return LibraryRepository(request.app.state.db)


def _user_accepted_terms(request: Request, user_id: str) -> bool:
    val = SettingRepository(request.app.state.db, user_id).get(TERMS_SETTING_KEY)
    return val == LIBRARY_TERMS_VERSION


def _is_admin_user(user: dict) -> bool:
    return (user.get("role") or "user") == "admin"


# ---- bodies ----

class SubmitItemBody(BaseModel):
    course_name: str = Field(..., min_length=2, max_length=120)
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field("", max_length=2000)
    url: str = Field(..., min_length=8, max_length=2000)
    topic_id: str | None = Field(None, max_length=64)


class TopicBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    sort_order: int = Field(0, ge=0, le=100000)


class TopicUpdateBody(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    sort_order: int | None = Field(None, ge=0, le=100000)


class ItemUpdateBody(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    url: str | None = Field(None, min_length=8, max_length=2000)
    topic_id: str | None = Field(None, max_length=64)
    clear_topic: bool = False


class RatingBody(BaseModel):
    score: int = Field(..., ge=1, le=5)


class CommentBody(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class ReportBody(BaseModel):
    reason: str = Field("", max_length=500)


class StatusBody(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|pending)$")


class CatalogCourseBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field("", max_length=40)
    term: str = Field("", max_length=20)
    sort_order: int = Field(0, ge=0, le=100000)


class CatalogBulkBody(BaseModel):
    courses: list[CatalogCourseBody] = Field(..., min_length=1, max_length=500)


class CatalogUpdateBody(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    code: str | None = Field(None, max_length=40)
    term: str | None = Field(None, max_length=20)
    is_active: bool | None = None
    sort_order: int | None = Field(None, ge=0, le=100000)


# ---- public / user endpoints ----

@router.get("/courses")
async def list_courses(request: Request, term: str | None = None, scope: str = "all") -> dict:
    """لیست درس‌های کتابخانه.

    scope=all → فقط درس‌هایی که حداقل یک منبع تاییدشده دارند
    scope=current_term / my_courses → فقط دروس فعال ثبت‌نام‌شده کاربر
      که در کاتالوگ هم هستند (match با نام یا کد)
    """
    user = get_current_user(request)
    repo = _repo(request)

    if scope in ("current_term", "my_courses"):
        from src.storage.repositories.course_repo import CourseRepository

        user_courses = CourseRepository(request.app.state.db, user["id"]).get_active()
        names = [c.name for c in user_courses if c.name]
        codes = [c.code for c in user_courses if c.code]
        courses = repo.filter_catalog_by_user_courses(names, codes)
        filter_term = None
    else:
        # all → فقط با منبع
        courses = repo.list_courses_with_items()
        filter_term = (term or "").strip() or None
        if filter_term:
            courses = [c for c in courses if (c.get("term") or "") == filter_term]

    return {
        "ok": True,
        "scope": scope,
        "term": filter_term,
        "available_terms": repo.list_terms(),
        "courses": [
            {
                "id": c.get("id"),
                "course_name": c["course_name"],
                "code": c.get("code") or "",
                "term": c.get("term") or "",
                "item_count": c["item_count"],
                "last_activity": c["last_activity"],
            }
            for c in courses
        ],
    }


@router.get("/course-names")
async def course_names_autocomplete(request: Request) -> dict:
    get_current_user(request)
    return {"ok": True, "names": _repo(request).list_course_names_for_autocomplete()}


@router.get("/courses/{course_name}")
async def list_items_for_course(
    request: Request,
    course_name: str,
    topic_id: str | None = None,
    uncategorized: bool = False,
) -> dict:
    user = get_current_user(request)
    repo = _repo(request)
    topics = repo.list_topics(course_name)
    items = repo.list_approved_for_course(
        course_name,
        topic_id=topic_id,
        uncategorized_only=uncategorized and not topic_id,
    )
    is_admin = _is_admin_user(user)
    result = []
    for it in items:
        my_rating = repo.get_user_rating(it["id"], user["id"])
        is_owner = it.get("submitted_by") == user["id"]
        result.append(
            {
                "id": it["id"],
                "course_name": it["course_name"],
                "title": it["title"],
                "description": it["description"],
                "url": it["url"],
                "avg_rating": it["avg_rating"],
                "rating_count": it["rating_count"],
                "report_count": it["report_count"],
                "submitter_name": it.get("submitter_name"),
                "submitted_by": it.get("submitted_by"),
                "created_at": it["created_at"],
                "my_rating": my_rating,
                "topic_id": it.get("topic_id"),
                "topic_title": it.get("topic_title"),
                "can_edit": is_admin or is_owner,
                "can_assign_topic": is_admin,
            }
        )
    return {
        "ok": True,
        "course_name": course_name,
        "topics": [
            {
                "id": t["id"],
                "title": t["title"],
                "sort_order": t.get("sort_order") or 0,
                "item_count": t.get("item_count") or 0,
            }
            for t in topics
        ],
        "items": result,
        "active_topic_id": topic_id,
    }


@router.get("/courses/{course_name}/topics")
async def list_course_topics(request: Request, course_name: str) -> dict:
    get_current_user(request)
    topics = _repo(request).list_topics(course_name)
    return {
        "ok": True,
        "course_name": course_name,
        "topics": [
            {
                "id": t["id"],
                "title": t["title"],
                "sort_order": t.get("sort_order") or 0,
                "item_count": t.get("item_count") or 0,
            }
            for t in topics
        ],
    }


@router.post("/admin/courses/{course_name}/topics")
async def admin_create_topic(request: Request, course_name: str, body: TopicBody) -> dict:
    admin = require_admin(request)
    try:
        row = _repo(request).create_topic(
            course_name=course_name,
            title=body.title,
            sort_order=body.sort_order,
            created_by=admin["id"],
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "topic": {
            "id": row["id"],
            "course_name": row["course_name"],
            "title": row["title"],
            "sort_order": row.get("sort_order") or 0,
        },
    }


@router.patch("/admin/topics/{topic_id}")
async def admin_update_topic(request: Request, topic_id: str, body: TopicUpdateBody) -> dict:
    require_admin(request)
    try:
        row = _repo(request).update_topic(
            topic_id,
            title=body.title,
            sort_order=body.sort_order,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not row:
        raise HTTPException(404, "تاپیک یافت نشد")
    return {
        "ok": True,
        "topic": {
            "id": row["id"],
            "course_name": row["course_name"],
            "title": row["title"],
            "sort_order": row.get("sort_order") or 0,
        },
    }


@router.delete("/admin/topics/{topic_id}")
async def admin_delete_topic(request: Request, topic_id: str) -> dict:
    require_admin(request)
    ok = _repo(request).delete_topic(topic_id)
    if not ok:
        raise HTTPException(404, "تاپیک یافت نشد")
    return {"ok": True}


@router.get("/terms")
async def get_library_terms(request: Request) -> dict:
    """متن قوانین + وضعیت قبول کاربر. ادمین همیشه accepted=true."""
    user = get_current_user(request)
    is_admin = _is_admin_user(user)
    accepted = True if is_admin else _user_accepted_terms(request, user["id"])
    return {
        "ok": True,
        "version": LIBRARY_TERMS_VERSION,
        "text": LIBRARY_TERMS_TEXT,
        "accepted": accepted,
        "required": not is_admin,
        "is_admin": is_admin,
    }


@router.post("/terms/accept")
async def accept_library_terms(request: Request) -> dict:
    """ثبت قبول قوانین. برای ادمین no-op موفق."""
    user = get_current_user(request)
    if _is_admin_user(user):
        return {"ok": True, "accepted": True, "skipped": True, "reason": "admin"}
    SettingRepository(request.app.state.db, user["id"]).set(
        TERMS_SETTING_KEY, LIBRARY_TERMS_VERSION
    )
    return {"ok": True, "accepted": True, "version": LIBRARY_TERMS_VERSION}


@router.patch("/items/{item_id}")
async def update_item(request: Request, item_id: str, body: ItemUpdateBody) -> dict:
    """ویرایش منبع: ادمین یا ارسال‌کننده."""
    user = get_current_user(request)
    repo = _repo(request)
    item = repo.get_item(item_id)
    if not item:
        raise HTTPException(404, "منبع یافت نشد")
    is_admin = _is_admin_user(user)
    is_owner = item.get("submitted_by") == user["id"]
    if not (is_admin or is_owner):
        raise HTTPException(403, "فقط ادمین یا ارسال‌کننده می‌تواند ویرایش کند")
    # تغییر تاپیک فقط برای ادمین
    if (body.topic_id is not None or body.clear_topic) and not is_admin:
        raise HTTPException(403, "فقط ادمین می‌تواند تاپیک را تغییر دهد")
    try:
        updated = repo.update_item(
            item_id,
            title=body.title,
            description=body.description,
            url=body.url,
            topic_id=body.topic_id,
            clear_topic=body.clear_topic,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "item": {
            "id": updated["id"],
            "title": updated["title"],
            "description": updated.get("description") or "",
            "url": updated["url"],
            "topic_id": updated.get("topic_id"),
            "course_name": updated["course_name"],
        },
    }


@router.post("/items")
async def submit_item(request: Request, body: SubmitItemBody) -> dict:
    user = get_current_user(request)
    # ادمین نیازی به قبول قوانین ندارد؛ بقیه باید قبول کرده باشند
    if not _is_admin_user(user) and not _user_accepted_terms(request, user["id"]):
        raise HTTPException(
            403,
            "قبل از ارسال منبع باید قوانین کتابخانه را بپذیرید",
        )
    try:
        item = _repo(request).create_item(
            course_name=body.course_name,
            title=body.title,
            description=body.description,
            url=body.url,
            user_id=user["id"],
            topic_id=body.topic_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "item": {
            "id": item["id"],
            "course_name": item["course_name"],
            "title": item["title"],
            "status": item["status"],
            "topic_id": item.get("topic_id"),
            "created_at": item["created_at"],
        },
        "message": "ارسال شد و پس از تایید ادمین نمایش داده می‌شود",
    }


@router.get("/items/{item_id}")
async def get_item_detail(request: Request, item_id: str) -> dict:
    user = get_current_user(request)
    repo = _repo(request)
    item = repo.get_item(item_id)
    if not item:
        raise HTTPException(404, "مورد یافت نشد")
    is_admin = (user.get("role") or "") == "admin"
    if item["status"] != "approved" and item["submitted_by"] != user["id"] and not is_admin:
        raise HTTPException(404, "مورد یافت نشد")

    comments = repo.list_comments(item_id) if item["status"] == "approved" else []
    my_rating = repo.get_user_rating(item_id, user["id"]) if item["status"] == "approved" else None
    is_owner = item.get("submitted_by") == user["id"]
    return {
        "ok": True,
        "item": {
            "id": item["id"],
            "course_name": item["course_name"],
            "title": item["title"],
            "description": item["description"],
            "url": item["url"],
            "status": item["status"],
            "avg_rating": item["avg_rating"],
            "rating_count": item["rating_count"],
            "report_count": item["report_count"],
            "submitter_name": item.get("submitter_name"),
            "submitted_by": item.get("submitted_by"),
            "topic_id": item.get("topic_id"),
            "created_at": item["created_at"],
            "my_rating": my_rating,
            "can_edit": is_admin or is_owner,
            "can_assign_topic": is_admin,
        },
        "comments": [
            {
                "id": c["id"],
                "body": c["body"],
                "author_name": c.get("author_name"),
                "created_at": c["created_at"],
            }
            for c in comments
        ],
    }


@router.post("/items/{item_id}/rating")
async def rate_item(request: Request, item_id: str, body: RatingBody) -> dict:
    user = get_current_user(request)
    try:
        item = _repo(request).set_rating(item_id, user["id"], body.score)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "avg_rating": item["avg_rating"],
        "rating_count": item["rating_count"],
        "my_rating": body.score,
    }


@router.post("/items/{item_id}/comments")
async def add_comment(request: Request, item_id: str, body: CommentBody) -> dict:
    user = get_current_user(request)
    try:
        comment = _repo(request).add_comment(item_id, user["id"], body.body)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "comment": {
            "id": comment["id"],
            "body": comment["body"],
            "author_name": comment.get("author_name") or user.get("full_name"),
            "created_at": comment["created_at"],
        },
    }


@router.post("/items/{item_id}/report")
async def report_item(request: Request, item_id: str, body: ReportBody) -> dict:
    user = get_current_user(request)
    try:
        item = _repo(request).report_item(item_id, user["id"], body.reason)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True, "report_count": item["report_count"], "message": "گزارش ثبت شد"}


@router.get("/my-submissions")
async def my_submissions(request: Request) -> dict:
    user = get_current_user(request)
    items = _repo(request).list_my_submissions(user["id"])
    return {
        "ok": True,
        "items": [
            {
                "id": i["id"],
                "course_name": i["course_name"],
                "title": i["title"],
                "url": i["url"],
                "status": i["status"],
                "created_at": i["created_at"],
            }
            for i in items
        ],
    }


# ---- admin: catalog ----

@router.get("/admin/catalog")
async def admin_list_catalog(request: Request) -> dict:
    require_admin(request)
    courses = _repo(request).list_catalog(include_inactive=True)
    return {
        "ok": True,
        "courses": [
            {
                "id": c["id"],
                "name": c["course_name"],
                "code": c.get("code") or "",
                "term": c.get("term") or "",
                "is_active": bool(c.get("is_active")),
                "sort_order": c.get("sort_order") or 0,
                "item_count": c.get("item_count") or 0,
            }
            for c in courses
        ],
        "available_terms": _repo(request).list_terms(),
    }


@router.post("/admin/catalog")
async def admin_add_catalog_course(request: Request, body: CatalogCourseBody) -> dict:
    admin = require_admin(request)
    try:
        row = _repo(request).create_catalog_course(
            name=body.name,
            code=body.code,
            term=body.term,
            sort_order=body.sort_order,
            created_by=admin["id"],
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ok": True,
        "course": {
            "id": row["id"],
            "name": row["name"],
            "code": row["code"],
            "term": row["term"],
        },
    }


@router.post("/admin/catalog/bulk")
async def admin_bulk_catalog(request: Request, body: CatalogBulkBody) -> dict:
    admin = require_admin(request)
    result = _repo(request).bulk_create_catalog(
        [c.model_dump() for c in body.courses],
        created_by=admin["id"],
    )
    return {"ok": True, **result}


@router.patch("/admin/catalog/{course_id}")
async def admin_update_catalog(request: Request, course_id: str, body: CatalogUpdateBody) -> dict:
    require_admin(request)
    try:
        row = _repo(request).update_catalog_course(
            course_id,
            name=body.name,
            code=body.code,
            term=body.term,
            is_active=body.is_active,
            sort_order=body.sort_order,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not row:
        raise HTTPException(404, "درس یافت نشد")
    return {
        "ok": True,
        "course": {
            "id": row["id"],
            "name": row["name"],
            "code": row["code"],
            "term": row["term"],
            "is_active": bool(row["is_active"]),
        },
    }


@router.delete("/admin/catalog/{course_id}")
async def admin_delete_catalog(request: Request, course_id: str) -> dict:
    require_admin(request)
    ok = _repo(request).delete_catalog_course(course_id)
    if not ok:
        raise HTTPException(404, "درس یافت نشد")
    return {"ok": True}


# ---- admin: moderation ----

@router.get("/admin/pending")
async def admin_pending(request: Request) -> dict:
    require_admin(request)
    items = _repo(request).list_pending()
    return {
        "ok": True,
        "items": [
            {
                "id": i["id"],
                "course_name": i["course_name"],
                "title": i["title"],
                "description": i["description"],
                "url": i["url"],
                "submitter_name": i.get("submitter_name"),
                "submitter_username": i.get("submitter_username"),
                "created_at": i["created_at"],
            }
            for i in items
        ],
    }


@router.post("/admin/items/{item_id}/status")
async def admin_set_status(request: Request, item_id: str, body: StatusBody) -> dict:
    admin = require_admin(request)
    item = _repo(request).set_status(item_id, body.status, admin_user_id=admin["id"])
    if not item:
        raise HTTPException(404, "مورد یافت نشد")
    return {"ok": True, "id": item["id"], "status": item["status"]}


@router.delete("/admin/items/{item_id}")
async def admin_delete_item(request: Request, item_id: str) -> dict:
    require_admin(request)
    ok = _repo(request).delete_item(item_id)
    if not ok:
        raise HTTPException(404, "مورد یافت نشد")
    return {"ok": True}


@router.get("/admin/reports")
async def admin_reports(request: Request) -> dict:
    require_admin(request)
    reports = _repo(request).list_open_reports()
    return {
        "ok": True,
        "reports": [
            {
                "id": r["id"],
                "item_id": r["item_id"],
                "item_title": r["item_title"],
                "item_url": r["item_url"],
                "course_name": r["course_name"],
                "item_status": r["item_status"],
                "reason": r["reason"],
                "reporter_name": r.get("reporter_name"),
                "reporter_username": r.get("reporter_username"),
                "created_at": r["created_at"],
            }
            for r in reports
        ],
    }


@router.post("/admin/reports/{report_id}/resolve")
async def admin_resolve_report(request: Request, report_id: str) -> dict:
    require_admin(request)
    ok = _repo(request).resolve_report(report_id)
    if not ok:
        raise HTTPException(404, "گزارش یافت نشد")
    return {"ok": True}
