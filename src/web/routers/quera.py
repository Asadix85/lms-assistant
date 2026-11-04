"""Router داده‌های Quera."""

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from src.storage.repositories import QueraAssignmentRepository, QueraCourseRepository
from src.storage.repositories.user_repo import UserRepository
from src.web.security import SESSION_COOKIE_NAME
from fastapi import HTTPException
from src.web.schemas import QueraAssignmentOut, QueraCourseOut

router = APIRouter()

def _require_user(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(401, "ابتدا وارد شوید")
    user = UserRepository(request.app.state.db).get_user_by_token(token)
    if not user:
        raise HTTPException(401, "نشست منقضی شده است")
    return user




@router.get("/assignments", response_model=list[QueraAssignmentOut])
async def list_assignments(request: Request) -> list[QueraAssignmentOut]:
    repo = QueraAssignmentRepository(request.app.state.db, _require_user(request)["id"])
    return [QueraAssignmentOut.from_model(a) for a in repo.get_all()]


@router.get("/courses", response_model=list[QueraCourseOut])
async def list_courses(request: Request) -> list[QueraCourseOut]:
    repo = QueraCourseRepository(request.app.state.db, _require_user(request)["id"])
    return [QueraCourseOut.from_model(c) for c in repo.get_all()]


@router.post("/assignments/{assignment_id}/done")
async def set_done(request: Request, assignment_id: str, done: bool = True) -> dict:
    repo = QueraAssignmentRepository(request.app.state.db, _require_user(request)["id"])
    if not repo.exists(assignment_id):
        return {"ok": False, "error": "یافت نشد"}
    repo.set_done(assignment_id, done)
    return {"ok": True}


@router.post("/sync")
async def sync_quera(request: Request) -> dict:
    """اجرای sync Quera (لاگین + دریافت تمرین‌ها)."""
    session = request.app.state.session
    result = await run_in_threadpool(session.run_quera_sync)
    return {"ok": result.get("error") is None, **result}
