"""Router داده‌های Quera."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from src.storage.repositories import QueraAssignmentRepository, QueraCourseRepository
from src.storage.repositories.user_repo import UserRepository
from src.web.security import SESSION_COOKIE_NAME
from src.web.schemas import QueraAssignmentOut, QueraCourseOut

router = APIRouter()


def _require_user(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "ابتدا وارد شوید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise HTTPException(401, "نشست منقضی شده است")
    return user


@router.get("/assignments", response_model=list[QueraAssignmentOut])
async def list_assignments(request: Request) -> list[QueraAssignmentOut]:
    repo = QueraAssignmentRepository(request.app.state.db, _require_user(request)["id"])
    return [QueraAssignmentOut.from_model(a) for a in repo.get_all()]


@router.get("/courses", response_model=list[QueraCourseOut])
async def list_courses(request: Request) -> list[QueraCourseOut]:
    repo = QueraCourseRepository(request.app.state.db, _require_user(request)["id"])
    return [QueraCourseOut.from_model(c) for c in repo.get_all()]


@router.post("/assignments/{assignment_id}/done")
async def set_done(request: Request, assignment_id: str, done: bool = True) -> dict:
    repo = QueraAssignmentRepository(request.app.state.db, _require_user(request)["id"])
    if not repo.exists(assignment_id):
        return {"ok": False, "error": "یافت نشد"}
    repo.set_done(assignment_id, done)
    return {"ok": True}


_QUERA_SYNCING: set[str] = set()


@router.post("/sync")
async def sync_quera(request: Request) -> dict:
    """اجرای sync Quera برای کاربر فعلی."""
    user = _require_user(request)
    session = request.app.state.session
    session.set_active_user(user["id"])

    if user["id"] in _QUERA_SYNCING:
        return {"ok": False, "error": "همگام‌سازی کوئرا از قبل در حال انجام است"}

    _QUERA_SYNCING.add(user["id"])
    try:
        result = await run_in_threadpool(session.run_quera_sync, user["id"])
    finally:
        _QUERA_SYNCING.discard(user["id"])

    return {"ok": result.get("error") is None, **result}

from pydantic import BaseModel, Field


class QueraCookieBody(BaseModel):
    cookie: str = Field(..., min_length=8, max_length=500)


@router.post("/cookie")
async def set_quera_cookie(request: Request, body: QueraCookieBody) -> dict:
    """ذخیره کوکی نشست کوئرا برای کاربر فعلی."""
    from src.storage.repositories.user_repo import UserRepository
    user = _require_user(request)
    repo = UserRepository(request.app.state.db)
    
    cookie_value = body.cookie.strip()
    if not cookie_value:
        return {"ok": False, "error": "کوکی نمی‌تواند خالی باشد"}
    
    # حذف پیشوند احتمالی
    if "=" in cookie_value:
        parts = cookie_value.split("=", 1)
        if parts[0].strip().lower() == "sessionid":
            cookie_value = parts[1].strip()
    
    # ذخیره کوکی در دیتابیس (در فیلد quera_password)
    secrets = repo.load_secrets(user["id"])
    repo.save_secrets(
        user["id"],
        lms_password=secrets.get("lms_password"),
        lms_cookies_json=secrets.get("lms_cookies_json"),
        quera_username=secrets.get("quera_username") or "cookie",
        quera_password=cookie_value,  # کوکی را اینجا ذخیره می‌کنیم
    )
    
    return {"ok": True, "message": "کوکی کوئرا ذخیره شد"}


@router.get("/cookie-status")
async def cookie_status(request: Request) -> dict:
    """بررسی وضعیت کوکی کوئرا."""
    from src.storage.repositories.user_repo import UserRepository
    user = _require_user(request)
    repo = UserRepository(request.app.state.db)
    secrets = repo.load_secrets(user["id"])
    
    has_cookie = bool(secrets.get("quera_password"))
    
    return {
        "ok": True,
        "has_cookie": has_cookie,
        "message": "کوکی تنظیم شده" if has_cookie else "کوکی تنظیم نشده"
    }