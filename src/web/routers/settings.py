"""Router تنظیمات: فازهای sync و تم (مخزن: SQLite settings)."""

from fastapi import APIRouter, Request

from fastapi import HTTPException
from src.storage.repositories import SettingRepository
from src.storage.repositories.user_repo import UserRepository
from src.web.security import SESSION_COOKIE_NAME

router = APIRouter()

def _require_user(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "ابتدا وارد شوید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise HTTPException(401, "نشست منقضی شده است")
    return user


SYNC_KEYS = {
    "courses": "sync_courses",
    "contents": "sync_contents",
    "events": "sync_events",
    "wall": "sync_wall",
    "members": "sync_members",
}


@router.get("/sync")
async def get_sync_settings(request: Request) -> dict:
    repo = SettingRepository(request.app.state.db, _require_user(request)["id"])
    return {
        ui_key: repo.get(db_key, "true" if ui_key != "members" else "false") == "true"
        for ui_key, db_key in SYNC_KEYS.items()
    }


@router.post("/sync")
async def save_sync_settings(request: Request, body: dict) -> dict:
    repo = SettingRepository(request.app.state.db, _require_user(request)["id"])
    for ui_key, value in (body or {}).items():
        db_key = SYNC_KEYS.get(ui_key)
        if db_key:
            repo.set(db_key, "true" if value else "false")
    return {"ok": True}


@router.get("/theme")
async def get_theme(request: Request) -> dict:
    repo = SettingRepository(request.app.state.db, _require_user(request)["id"])
    return {"theme": repo.get("app_theme", "light")}


@router.post("/theme")
async def save_theme(request: Request, body: dict) -> dict:
    repo = SettingRepository(request.app.state.db, _require_user(request)["id"])
    theme = body.get("theme", "light")
    if theme not in ("light", "dark"):
        theme = "light"
    repo.set("app_theme", theme)
    return {"ok": True, "theme": theme}
