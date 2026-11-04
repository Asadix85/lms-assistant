"""API پشتیبانی: گزارش باگ توسط کاربر + پاسخ ادمین."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.storage.repositories.support_repo import SupportRepository
from src.web.deps import get_current_user, require_admin

router = APIRouter()


class CreateTicketBody(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=5, max_length=5000)


class MessageBody(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class StatusBody(BaseModel):
    status: str = Field(..., pattern="^(open|answered|closed)$")


def _repo(request: Request) -> SupportRepository:
    return SupportRepository(request.app.state.db)


# ---- کاربر ----

@router.get("/tickets")
async def my_tickets(request: Request) -> dict:
    user = get_current_user(request)
    items = _repo(request).list_for_user(user["id"])
    return {
        "ok": True,
        "tickets": [
            {
                "id": t["id"],
                "subject": t["subject"],
                "status": t["status"],
                "created_at": t["created_at"],
                "updated_at": t["updated_at"],
                "message_count": t.get("message_count") or 0,
            }
            for t in items
        ],
    }


@router.post("/tickets")
async def create_ticket(request: Request, body: CreateTicketBody) -> dict:
    user = get_current_user(request)
    ticket = _repo(request).create_ticket(user["id"], body.subject, body.body)
    return {"ok": True, "ticket": {"id": ticket["id"], "subject": ticket["subject"], "status": ticket["status"]}}


@router.get("/tickets/{ticket_id}")
async def get_ticket(request: Request, ticket_id: str) -> dict:
    user = get_current_user(request)
    repo = _repo(request)
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "تیکت یافت نشد")
    is_admin = (user.get("role") or "") == "admin"
    if ticket["user_id"] != user["id"] and not is_admin:
        raise HTTPException(403, "دسترسی ندارید")
    messages = repo.list_messages(ticket_id)
    return {
        "ok": True,
        "ticket": {
            "id": ticket["id"],
            "subject": ticket["subject"],
            "status": ticket["status"],
            "user_id": ticket["user_id"],
            "created_at": ticket["created_at"],
            "updated_at": ticket["updated_at"],
        },
        "messages": [
            {
                "id": m["id"],
                "body": m["body"],
                "is_staff": bool(m["is_staff"]),
                "author_name": m.get("full_name") or ("پشتیبانی" if m["is_staff"] else "کاربر"),
                "created_at": m["created_at"],
            }
            for m in messages
        ],
    }


@router.post("/tickets/{ticket_id}/messages")
async def reply_ticket(request: Request, ticket_id: str, body: MessageBody) -> dict:
    user = get_current_user(request)
    repo = _repo(request)
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(404, "تیکت یافت نشد")
    is_admin = (user.get("role") or "") == "admin"
    if ticket["user_id"] != user["id"] and not is_admin:
        raise HTTPException(403, "دسترسی ندارید")
    if ticket["status"] == "closed" and not is_admin:
        raise HTTPException(400, "این تیکت بسته شده است")
    msg = repo.add_message(
        ticket_id,
        user["id"],
        body.body,
        is_staff=is_admin,
    )
    return {"ok": True, "message_id": msg["id"]}


# ---- ادمین ----

@router.get("/admin/tickets")
async def admin_list_tickets(request: Request, status: str | None = None) -> dict:
    require_admin(request)
    if status and status not in ("open", "answered", "closed"):
        raise HTTPException(400, "وضعیت نامعتبر")
    items = _repo(request).list_all(status=status)
    return {
        "ok": True,
        "tickets": [
            {
                "id": t["id"],
                "subject": t["subject"],
                "status": t["status"],
                "full_name": t.get("full_name"),
                "lms_username": t.get("lms_username"),
                "created_at": t["created_at"],
                "updated_at": t["updated_at"],
                "message_count": t.get("message_count") or 0,
            }
            for t in items
        ],
    }


@router.patch("/admin/tickets/{ticket_id}/status")
async def admin_set_status(request: Request, ticket_id: str, body: StatusBody) -> dict:
    require_admin(request)
    repo = _repo(request)
    if not repo.get_ticket(ticket_id):
        raise HTTPException(404, "تیکت یافت نشد")
    repo.set_status(ticket_id, body.status)
    return {"ok": True, "status": body.status}
