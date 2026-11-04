"""API پنل ادمین: لیست کاربران، نقش، فعال/غیرفعال، قطع نشست."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.storage.repositories.user_repo import UserRepository
from src.web.deps import require_admin
from src.web.security import MAX_ADMINS

router = APIRouter()


class RoleBody(BaseModel):
    role: str = Field(..., pattern="^(user|admin)$")


class ActiveBody(BaseModel):
    active: bool


def _repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.db)


@router.get("/users")
async def list_users(request: Request) -> dict:
    admin = require_admin(request)
    users = _repo(request).list_users()
    # هرگز پسورد/کوکی برنگردان
    safe = []
    for u in users:
        safe.append(
            {
                "id": u["id"],
                "lms_username": u["lms_username"],
                "full_name": u.get("full_name"),
                "role": u.get("role") or "user",
                "is_active": bool(u.get("is_active", 1)),
                "created_at": u.get("created_at"),
                "last_login_at": u.get("last_login_at"),
                "session_count": u.get("session_count") or 0,
                "is_self": u["id"] == admin["id"],
            }
        )
    return {
        "ok": True,
        "users": safe,
        "stats": {
            "total": len(safe),
            "admins": sum(1 for u in safe if u["role"] == "admin"),
            "inactive": sum(1 for u in safe if not u["is_active"]),
            "max_admins": MAX_ADMINS,
        },
    }


@router.patch("/users/{user_id}/role")
async def set_user_role(request: Request, user_id: str, body: RoleBody) -> dict:
    admin = require_admin(request)
    repo = _repo(request)
    target = repo.get_by_id(user_id)
    if not target:
        raise HTTPException(404, "کاربر یافت نشد")

    # آخرین ادمین را نمی‌توان از admin خارج کرد
    if target.get("role") == "admin" and body.role != "admin":
        if repo.count_admins() <= 1:
            raise HTTPException(400, "حداقل یک ادمین باید باقی بماند")

    # ادمین نباید خودش را از admin خارج کند اگر تنها ادمین است (بالا پوشش داده شد)
    try:
        ok = repo.set_role(user_id, body.role)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    if not ok:
        raise HTTPException(400, "به‌روزرسانی نقش ناموفق بود")

    return {"ok": True, "user_id": user_id, "role": body.role}


@router.patch("/users/{user_id}/active")
async def set_user_active(request: Request, user_id: str, body: ActiveBody) -> dict:
    admin = require_admin(request)
    repo = _repo(request)
    target = repo.get_by_id(user_id)
    if not target:
        raise HTTPException(404, "کاربر یافت نشد")

    if user_id == admin["id"] and not body.active:
        raise HTTPException(400, "نمی‌توانید حساب خودتان را غیرفعال کنید")

    if target.get("role") == "admin" and not body.active:
        if repo.count_admins() <= 1:
            raise HTTPException(400, "نمی‌توان آخرین ادمین را غیرفعال کرد")

    if not repo.set_active(user_id, body.active):
        raise HTTPException(400, "به‌روزرسانی وضعیت ناموفق بود")

    # قطع همه sessionها وقتی غیرفعال شد
    if not body.active:
        repo.delete_user_sessions(user_id)
        try:
            request.app.state.session.logout_user(user_id)
        except Exception:
            pass

    return {"ok": True, "user_id": user_id, "is_active": body.active}


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_sessions(request: Request, user_id: str) -> dict:
    admin = require_admin(request)
    repo = _repo(request)
    target = repo.get_by_id(user_id)
    if not target:
        raise HTTPException(404, "کاربر یافت نشد")

    repo.delete_user_sessions(user_id)
    try:
        request.app.state.session.logout_user(user_id)
    except Exception:
        pass

    return {"ok": True, "user_id": user_id, "revoked_by": admin["id"]}
