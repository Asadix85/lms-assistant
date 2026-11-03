"""Router Sync: شروع همگام‌سازی + استریم پیشرفت با SSE."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

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


@router.post("/start")
async def start_sync(request: Request) -> dict:
    """شروع sync کامل LMS در بک‌گراند برای کاربر لاگین‌شده."""
    user = _require_user(request)
    session = request.app.state.session
    session.set_active_user(user["id"])
    try:
        started = session.start_lms_sync(user["id"])
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    if not started:
        return {"ok": False, "error": "همگام‌سازی در حال انجام است"}
    return {"ok": True}


@router.get("/status")
async def sync_status(request: Request) -> dict:
    session = request.app.state.session
    p = session.latest_progress
    return {
        "running": session.sync_running,
        "progress": None
        if p is None
        else {
            "phase": p.phase,
            "percent": p.percent,
            "message": p.message,
            "current": p.current,
            "total": p.total,
            "changes": p.changes,
        },
        "last_result": None
        if session.last_result is None
        else {
            "error": session.last_result.error,
            "duration": session.last_result.duration_seconds,
            "summary": session.last_result.summary(),
        },
    }


@router.get("/stream")
async def stream_sync(request: Request) -> StreamingResponse:
    """SSE: رویدادهای زنده پیشرفت sync را به مرورگر می‌فرستد."""
    session = request.app.state.session
    queue = session.subscribe()

    async def event_gen():
        try:
            yield "event: hello\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    payload = json.dumps(event, ensure_ascii=False)
                    yield f"event: {event['type']}\ndata: {payload}\n\n"
                    if event["type"] in ("result", "error"):
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            session.unsubscribe(queue)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
