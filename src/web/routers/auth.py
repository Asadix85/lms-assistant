"""Router احراز هویت (LMS/Quera credentials)."""

from fastapi import APIRouter, Request

from src.web.schemas import LoginRequest, SessionStatus

router = APIRouter()


def _session(request: Request):
    return request.app.state.session


@router.get("/status", response_model=SessionStatus)
async def status(request: Request) -> SessionStatus:
    s = _session(request)
    creds = s.creds
    return SessionStatus(
        lms_logged_in=s.lms_logged_in or bool(creds.lms_username and creds.lms_password),
        quera_logged_in=bool(creds.quera_username and creds.quera_password),
        full_name=s.full_name,
        username=creds.lms_username or None,
    )


@router.post("/login")
async def login(request: Request, body: LoginRequest) -> dict:
    """ذخیره credentials و تلاش برای login به LMS."""
    s = _session(request)
    s.set_credentials(
        body.lms_username.strip(),
        body.lms_password,
        body.quera_username.strip(),
        body.quera_password,
    )
    try:
        s.get_assistant()
        return {"ok": True, "full_name": s.full_name}
    except PermissionError as e:
        return {"ok": False, "error": str(e)}


@router.post("/logout")
async def logout(request: Request) -> dict:
    _session(request).logout()
    return {"ok": True}


from fastapi import HTTPException


@router.get("/cookies")
async def get_session_cookies(request: Request) -> dict:
    """دریافت کوکی‌های معتبر برای تزریق در افزونه مرورگر."""
    s = _session(request)
    try:
        assistant = s.get_assistant()
    except PermissionError:
        raise HTTPException(401, "ابتدا لاگین کنید")

    if not assistant or not assistant.is_authenticated:
        raise HTTPException(401, "نشست منقضی شده است")

    # استخراج کوکی‌ها از کلاینت httpx
    cookies = []
    for cookie in assistant.client.cookies.jar:
        cookies.append({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "secure": cookie.secure,
            "httpOnly": cookie.has_nonstandard_attr('HttpOnly') or False,
            "sameSite": "no_restriction",  # یا "lax" / "strict"
        })

    return {"cookies": cookies}

from fastapi import HTTPException

@router.get("/credentials")
async def get_credentials(request: Request) -> dict:
    """دریافت اطلاعات لاگین برای افزونه (جهت پر کردن خودکار)."""
    s = _session(request)
    creds = s.creds
    if not creds.lms_username or not creds.lms_password:
        raise HTTPException(401, "اطلاعات لاگین تنظیم نشده است")
    return {
        "username": creds.lms_username,
        "password": creds.lms_password
    }