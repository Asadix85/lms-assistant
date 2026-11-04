"""Router احراز هویت وب: ورود با LMS → ساخت user + session cookie."""

from __future__ import annotations

import os

from fastapi import APIRouter, Request, Response
from loguru import logger

from src.services.lms_assistant import LMSAssistant
from src.storage.repositories.user_repo import UserRepository
from src.web.lms_cookies import dump_httpx_cookies
from src.web.rate_limit import login_ip_limiter, login_user_limiter
from src.web.schemas import LoginRequest, SessionStatus
from src.web.security import (
    SESSION_COOKIE_NAME,
    SESSION_DAYS,
    new_session_token,
    verify_password,
)

router = APIRouter()

COOKIE_SECURE = os.environ.get("LMS_COOKIE_SECURE", "0") in ("1", "true", "True")
REVOKE_OTHER_SESSIONS = os.environ.get("LMS_REVOKE_OTHER_SESSIONS", "1") in (
    "1",
    "true",
    "True",
)

def _admin_usernames() -> set[str]:
    """لیست یوزرنیم‌های LMS که باید ادمین شوند — از env."""
    raw = os.environ.get("LMS_ADMIN_USERNAMES", "").strip()
    if not raw:
        return set()
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _maybe_bootstrap_admin(repo: UserRepository, user: dict) -> dict:
    """اگر یوزرنیم در LMS_ADMIN_USERNAMES باشد یا هنوز هیچ ادمینی نباشد و این اولین کاربر است."""
    uname = (user.get("lms_username") or "").lower()
    admins_env = _admin_usernames()
    role = user.get("role") or "user"

    if uname in admins_env and role != "admin":
        repo.set_role(user["id"], "admin")
        user = repo.get_by_id(user["id"]) or user
        logger.info("کاربر به‌عنوان admin از طریق LMS_ADMIN_USERNAMES ارتقا یافت")
        return user

    # اگر هیچ ادمینی نیست و env خالی است: اولین لاگین‌کننده admin می‌شود (فقط یک‌بار)
    bootstrap = os.environ.get("LMS_BOOTSTRAP_FIRST_ADMIN", "0") in ("1", "true", "True")
    if bootstrap and repo.count_admins() == 0 and role != "admin":
        repo.set_role(user["id"], "admin")
        user = repo.get_by_id(user["id"]) or user
        logger.warning(
            "هیچ ادمینی نبود — این کاربر به‌عنوان اولین admin انتخاب شد. "
            "برای کنترل دقیق LMS_ADMIN_USERNAMES را ست کنید."
        )
    return user



def _user_repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.db)


def _session_mgr(request: Request):
    return request.app.state.session


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


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

    if int(user.get("is_active") if user.get("is_active") is not None else 1) == 0:
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
    1) rate-limit
    2) اعتبارسنجی واقعی روی LMS
    3) upsert کاربر + ذخیره کوکی LMS و پسورد رمزنگاری‌شده
    4) چرخش session سایت
    """
    username = (body.lms_username or "").strip()
    password = body.lms_password or ""
    if not username or not password:
        return {"ok": False, "error": "نام کاربری و رمز عبور LMS الزامی است"}

    ip = _client_ip(request)
    user_key = username.lower()

    if not login_ip_limiter.allow(f"ip:{ip}"):
        wait = login_ip_limiter.retry_after_seconds(f"ip:{ip}")
        logger.warning("rate-limit login IP={}", ip)
        return {
            "ok": False,
            "error": f"تلاش‌های ورود بیش از حد. حدود {wait} ثانیه دیگر دوباره امتحان کنید.",
        }
    if not login_user_limiter.allow(f"user:{user_key}"):
        wait = login_user_limiter.retry_after_seconds(f"user:{user_key}")
        logger.warning("rate-limit login user_len={}", len(username))
        return {
            "ok": False,
            "error": f"تلاش‌های ورود برای این حساب بیش از حد. حدود {wait} ثانیه صبر کنید.",
        }

    logger.info("تلاش ورود LMS (طول یوزرنیم={})", len(username))

    assistant = LMSAssistant(username, password)
    try:
        ok = assistant.login()
    except Exception as e:
        logger.error("خطای غیرمنتظره در لاگین LMS: {}", e)
        return {"ok": False, "error": "خطا در ارتباط با LMS"}

    if not ok:
        return {"ok": False, "error": "نام کاربری یا رمز عبور LMS نادرست است"}

    repo = _user_repo(request)
    try:
        repo.delete_expired_sessions()
    except Exception:
        pass

    user = repo.upsert_from_lms_login(
        lms_username=username,
        full_name=assistant.full_name,
        lms_user_id=assistant.user_id,
    )

    # حساب غیرفعال؟
    if int(user.get("is_active") if user.get("is_active") is not None else 1) == 0:
        logger.warning("تلاش ورود حساب غیرفعال user_id={}", user["id"])
        return {"ok": False, "error": "حساب شما توسط مدیر غیرفعال شده است"}

    user = _maybe_bootstrap_admin(repo, user)

    cookies_json = dump_httpx_cookies(assistant.client.cookies)
    repo.save_secrets(
        user["id"],
        lms_password=password,
        lms_cookies_json=cookies_json,
        quera_username=(body.quera_username or "").strip() or None,
        quera_password=body.quera_password or None,
    )

    if REVOKE_OTHER_SESSIONS:
        repo.delete_user_sessions(user["id"])

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


from pydantic import BaseModel, Field


class LocalLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/local-login")
async def local_login(request: Request, body: LocalLoginRequest, response: Response) -> dict:
    """ورود ادمین محلی با یوزرنیم/رمز (بدون LMS)."""
    username = (body.username or "").strip()
    password = body.password or ""
    if not username or not password:
        return {"ok": False, "error": "نام کاربری و رمز عبور الزامی است"}

    ip = _client_ip(request)
    if not login_ip_limiter.allow(f"ip:{ip}"):
        wait = login_ip_limiter.retry_after_seconds(f"ip:{ip}")
        return {"ok": False, "error": f"تلاش بیش از حد. {wait} ثانیه صبر کنید."}
    if not login_user_limiter.allow(f"local:{username.lower()}"):
        wait = login_user_limiter.retry_after_seconds(f"local:{username.lower()}")
        return {"ok": False, "error": f"تلاش بیش از حد. {wait} ثانیه صبر کنید."}

    repo = _user_repo(request)
    user = repo.get_by_local_username(username)
    if not user or not user.get("password_hash"):
        return {"ok": False, "error": "نام کاربری یا رمز عبور نادرست است"}
    if not verify_password(password, user["password_hash"]):
        return {"ok": False, "error": "نام کاربری یا رمز عبور نادرست است"}
    if int(user.get("is_active") if user.get("is_active") is not None else 1) == 0:
        return {"ok": False, "error": "حساب غیرفعال است"}

    if REVOKE_OTHER_SESSIONS:
        repo.delete_user_sessions(user["id"])
    try:
        repo.delete_expired_sessions()
    except Exception:
        pass

    raw_token = new_session_token()
    repo.create_session(user["id"], raw_token, user_agent=request.headers.get("user-agent"))
    repo.touch_last_login(user["id"])
    _set_session_cookie(response, raw_token)

    return {
        "ok": True,
        "full_name": user.get("full_name") or "مدیر سیستم",
        "username": user.get("lms_username"),
        "role": user.get("role") or "admin",
    }

