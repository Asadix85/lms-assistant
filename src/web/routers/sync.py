"""Router Sync: شروع همگام‌سازی + استریم پیشرفت با SSE (per-user)."""

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
    user = _require_user(request)
    session = request.app.state.session
    session.set_active_user(user["id"])
    try:
        started = session.start_lms_sync(user["id"])
    except PermissionError as e:
        return {"ok": False, "error": str(e)}
    if not started:
        return {"ok": False, "error": "همگام‌سازی شما از قبل در حال انجام است"}
    return {"ok": True}


@router.get("/status")
async def sync_status(request: Request) -> dict:
    user = _require_user(request)
    session = request.app.state.session
    session.set_active_user(user["id"])
    p = session.latest_progress_for(user["id"])
    last_mem = session.last_result_for(user["id"])
    last = session.get_last_sync(user["id"])
    return {
        "running": session.is_sync_running(user["id"]),
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
        if last_mem is None
        else {
            "error": last_mem.error,
            "duration": last_mem.duration_seconds,
            "summary": last_mem.summary(),
        },
        "last_sync": last,
    }


@router.get("/stream")
async def stream_sync(request: Request) -> StreamingResponse:
    user = _require_user(request)
    session = request.app.state.session
    session.set_active_user(user["id"])
    queue = session.subscribe(user["id"])

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
            session.unsubscribe(queue, user_id=user["id"])

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
