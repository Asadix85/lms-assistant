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
