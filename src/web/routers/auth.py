"""Router احراز هویت وب: ورود با LMS → ساخت user + session cookie."""

from __future__ import annotations

import os

from fastapi import APIRouter, Request, Response
from loguru import logger

from src.services.lms_assistant import LMSAssistant
from src.storage.repositories.user_repo import UserRepository
from src.web.schemas import LoginRequest, SessionStatus
from src.web.security import (
    SESSION_COOKIE_NAME,
    SESSION_DAYS,
    new_session_token,
)

router = APIRouter()

# در production روی HTTPS باید True باشد
COOKIE_SECURE = os.environ.get("LMS_COOKIE_SECURE", "0") in ("1", "true", "True")


def _user_repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.db)


def _session_mgr(request: Request):
    return request.app.state.session


def _set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


@router.get("/status", response_model=SessionStatus)
async def status(request: Request) -> SessionStatus:
    repo = _user_repo(request)
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return SessionStatus(
            lms_logged_in=False,
            quera_logged_in=False,
            full_name=None,
            username=None,
        )

    user = repo.get_user_by_token(token)
    if not user:
        return SessionStatus(
            lms_logged_in=False,
            quera_logged_in=False,
            full_name=None,
            username=None,
        )

    sm = _session_mgr(request)
    sm.set_active_user(user["id"])
    secrets = repo.load_secrets(user["id"])
    lms_live = sm.is_lms_live(user["id"])
    return SessionStatus(
        lms_logged_in=True,
        quera_logged_in=bool(secrets.get("quera_username") and secrets.get("quera_password")),
        full_name=user.get("full_name") or sm.full_name_for(user["id"]),
        username=user.get("lms_username"),
        lms_session_live=lms_live,
        role=user.get("role") or "user",
    )


@router.post("/login")
async def login(request: Request, body: LoginRequest, response: Response) -> dict:
    """
    ورود با حساب LMS:
    1) اعتبارسنجی واقعی روی LMS
    2) upsert کاربر سایت
    3) ذخیره اسرار رمزنگاری‌شده
    4) صدور session cookie سایت
    """
    username = (body.lms_username or "").strip()
    password = body.lms_password or ""
    if not username or not password:
        return {"ok": False, "error": "نام کاربری و رمز عبور LMS الزامی است"}

    logger.info("تلاش ورود LMS برای کاربر (طول یوزرنیم={})", len(username))

    assistant = LMSAssistant(username, password)
    try:
        ok = assistant.login()
    except Exception as e:
        logger.error("خطای غیرمنتظره در لاگین LMS: {}", e)
        return {"ok": False, "error": "خطا در ارتباط با LMS"}

    if not ok:
        return {"ok": False, "error": "نام کاربری یا رمز عبور LMS نادرست است"}

    repo = _user_repo(request)
    user = repo.upsert_from_lms_login(
        lms_username=username,
        full_name=assistant.full_name,
        lms_user_id=assistant.user_id,
    )

    repo.save_secrets(
        user["id"],
        lms_password=password,
        quera_username=(body.quera_username or "").strip() or None,
        quera_password=body.quera_password or None,
    )

    raw_token = new_session_token()
    ua = request.headers.get("user-agent")
    repo.create_session(user["id"], raw_token, user_agent=ua)

    sm = _session_mgr(request)
    sm.bind_assistant(user["id"], assistant)

    _set_session_cookie(response, raw_token)

    return {
        "ok": True,
        "full_name": user.get("full_name") or assistant.full_name,
        "username": user.get("lms_username"),
        "role": user.get("role") or "user",
    }


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    repo = _user_repo(request)
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        user = repo.get_user_by_token(token)
        repo.delete_session_by_token(token)
        if user:
            _session_mgr(request).logout_user(user["id"])
    _clear_session_cookie(response)
    return {"ok": True}
