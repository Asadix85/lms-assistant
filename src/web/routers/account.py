"""مدیریت حساب خود کاربر: نشست‌ها، export، حذف."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from src.storage.repositories.user_repo import UserRepository
from src.web.deps import get_current_user
from src.web.security import SESSION_COOKIE_NAME
from src.web.static_export import build_bundle

router = APIRouter()


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(request: Request, response: Response) -> dict:
    """خروج از همه دستگاه‌ها (نشست فعلی هم باطل می‌شود)."""
    user = get_current_user(request)
    repo = UserRepository(request.app.state.db)
    repo.delete_user_sessions(user["id"])
    try:
        request.app.state.session.logout_user(user["id"])
    except Exception:
        pass
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/export")
async def export_my_data(request: Request):
    """خروجی JSON از داده‌های شخصی (بدون پسورد/اسرار)."""
    user = get_current_user(request)
    bundle = build_bundle(
        request.app.state.db,
        user_id=user["id"],
        full_name=user.get("full_name"),
        username=user.get("lms_username"),
        source="export",
    )
    # هرگز اسرار را در export نگذار
    safe = {
        "user": {
            "id": user["id"],
            "lms_username": user.get("lms_username"),
            "full_name": user.get("full_name"),
            "role": user.get("role"),
            "created_at": user.get("created_at"),
        },
        "data": {k: v for k, v in bundle.items() if k not in ("secrets", "password")},
    }
    body = json.dumps(safe, ensure_ascii=False, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="lms-my-data.json"'},
    )


@router.delete("")
async def delete_my_account(request: Request, response: Response) -> dict:
    """حذف کامل حساب و دادهٔ کاربر."""
    user = get_current_user(request)
    # ادمین تنها را حذف نکن
    repo = UserRepository(request.app.state.db)
    if (user.get("role") or "") == "admin" and repo.count_admins() <= 1:
        raise HTTPException(400, "آخرین ادمین نمی‌تواند حساب خود را حذف کند")
    try:
        request.app.state.session.logout_user(user["id"])
    except Exception:
        pass
    repo.delete_user_account(user["id"])
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}
