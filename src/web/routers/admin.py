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

    _audit(request, admin["id"], "set_role", target=user_id, detail=body.role)
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

    _audit(request, admin["id"], "set_active", target=user_id, detail=str(body.active))
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

    _audit(request, admin["id"], "revoke_sessions", target=user_id)
    return {"ok": True, "user_id": user_id, "revoked_by": admin["id"]}


from pathlib import Path
import shutil
from datetime import datetime

from fastapi.responses import FileResponse

from src.storage.repositories.audit_repo import AuditRepository
from src.storage.repositories.setting_repo import SettingRepository
from config.settings import settings

SYSTEM_USER = "__system__"


class MaintenanceBody(BaseModel):
    enabled: bool
    message: str | None = None


def _audit(request: Request, actor_id: str, action: str, target: str | None = None, detail: str | None = None) -> None:
    try:
        AuditRepository(request.app.state.db).log(
            actor_user_id=actor_id,
            action=action,
            target_user_id=target,
            detail=detail,
        )
    except Exception:
        pass


@router.get("/system")
async def system_status(request: Request) -> dict:
    require_admin(request)
    srepo = SettingRepository(request.app.state.db, SYSTEM_USER)
    return {
        "ok": True,
        "maintenance": srepo.get("maintenance", "0") == "1",
        "maintenance_message": srepo.get("maintenance_message", "") or "",
        "max_admins": MAX_ADMINS,
    }


@router.post("/system/maintenance")
async def set_maintenance(request: Request, body: MaintenanceBody) -> dict:
    admin = require_admin(request)
    srepo = SettingRepository(request.app.state.db, SYSTEM_USER)
    srepo.set("maintenance", "1" if body.enabled else "0")
    if body.message is not None:
        srepo.set("maintenance_message", body.message)
    _audit(
        request,
        admin["id"],
        "maintenance_on" if body.enabled else "maintenance_off",
        detail=body.message,
    )
    return {
        "ok": True,
        "maintenance": body.enabled,
        "message": body.message or srepo.get("maintenance_message", ""),
    }


@router.get("/audit")
async def list_audit(request: Request, limit: int = 50) -> dict:
    require_admin(request)
    limit = max(1, min(limit, 200))
    rows = AuditRepository(request.app.state.db).list_recent(limit)
    return {
        "ok": True,
        "items": [
            {
                "id": r["id"],
                "action": r["action"],
                "actor_username": r.get("actor_username"),
                "actor_name": r.get("actor_name"),
                "target_user_id": r.get("target_user_id"),
                "detail": r.get("detail"),
                "created_at": r.get("created_at"),
            }
            for r in rows
        ],
    }


@router.post("/backup")
async def create_backup(request: Request) -> dict:
    admin = require_admin(request)
    db_path = Path(settings.db_path)
    if not db_path.exists():
        raise HTTPException(404, "فایل دیتابیس یافت نشد")
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"lms_{stamp}.db"
    shutil.copy2(db_path, dest)
    _audit(request, admin["id"], "backup", detail=str(dest.name))
    return {
        "ok": True,
        "filename": dest.name,
        "path": str(dest),
        "size_bytes": dest.stat().st_size,
        "download": f"/api/admin/backup/download/{dest.name}",
    }


@router.get("/backup/download/{filename}")
async def download_backup(request: Request, filename: str):
    require_admin(request)
    # فقط نام فایل ساده
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "نام فایل نامعتبر")
    db_path = Path(settings.db_path)
    path = (db_path.parent / "backups" / filename).resolve()
    if not str(path).startswith(str((db_path.parent / "backups").resolve())):
        raise HTTPException(400, "مسیر نامعتبر")
    if not path.exists():
        raise HTTPException(404, "بکاپ یافت نشد")
    return FileResponse(path, filename=filename, media_type="application/octet-stream")

