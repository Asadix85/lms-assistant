"""App اصلی FastAPI وب LMS Assistant."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config.settings import settings
from src.storage.database import Database
from src.storage.migrations import migrate
from src.web.routers import admin, auth, courses, proxy, quera, support
from src.web.routers import settings as settings_router
from src.web.routers import sync
from src.web.admin_bootstrap import ensure_local_admin
from src.web.session import SessionManager

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


def _prepare_db() -> Database:
    db_path = Path(settings.db_path)
    db = Database(db_path)
    db.connect()
    try:
        has_tables = db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='courses'"
        )
    except Exception:
        has_tables = None
    if has_tables is None:
        db.init_schema()
    else:
        # DB از قبل هست → فقط مهاجرت‌های جدید (مثل users)
        try:
            migrate(db.connection)
            db.connection.commit()
        except Exception as e:
            logger.error("خطا در migrate هنگام startup: {}", e)
            raise
    return db


def _cors_origins() -> list[str]:
    raw = os.environ.get("LMS_CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # توسعه محلی
    return [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = _prepare_db()
    session = SessionManager(db)
    session.attach_loop(asyncio.get_running_loop())

    app.state.db = db
    app.state.session = session
    app.state.lms_assistant = None

    try:
        ensure_local_admin(db)
    except Exception as e:
        logger.error("bootstrap ادمین محلی ناموفق: {}", e)

    # در production اگر SECRET_KEY پیش‌فرض باشد هشدار شدید
    if os.environ.get("LMS_ENV", "").lower() in ("prod", "production"):
        from src.web.security import get_secret_key
        if get_secret_key().startswith("dev-only"):
            logger.error(
                "LMS_ENV=production ولی LMS_SECRET_KEY تنظیم نشده — اسرار ناامن‌اند!"
            )

    yield
    db.close()


app = FastAPI(
    title="LMS Assistant Web",
    description="نسخه وب دستیار LMS دانشگاه اصفهان (FastAPI + HTML/CSS)",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(support.router, prefix="/api/support", tags=["support"])
app.include_router(courses.router, prefix="/api", tags=["lms"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(quera.router, prefix="/api/quera", tags=["quera"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(proxy.router, prefix="/api", tags=["proxy"])

app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
if ASSETS_DIR.exists():
    app.mount("/fonts", StaticFiles(directory=str(ASSETS_DIR / "fonts")), name="fonts")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/manifest.webmanifest", include_in_schema=False)
async def web_manifest() -> FileResponse:
    return FileResponse(
        str(WEB_DIR / "manifest.webmanifest"),
        media_type="application/manifest+json",
    )


@app.get("/sw.js", include_in_schema=False)
async def service_worker() -> FileResponse:
    return FileResponse(
        str(WEB_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    """اگر maintenance روشن باشد، APIهای غیر ادمین/استاتیک را قطع می‌کند."""
    path = request.url.path or ""
    # اجازه به استاتیک، لاگین، status، و خود admin
    allow_prefixes = (
        "/static",
        "/api/auth",
        "/api/admin",
        "/docs",
        "/openapi.json",
        "/favicon",
    )
    if path == "/" or path.startswith(allow_prefixes):
        return await call_next(request)

    try:
        db = getattr(request.app.state, "db", None)
        if db is None:
            return await call_next(request)
        from src.storage.repositories.setting_repo import SettingRepository
        srepo = SettingRepository(db, "__system__")
        if srepo.get("maintenance", "0") != "1":
            return await call_next(request)
        # ادمین لاگین‌شده عبور کند
        from src.web.deps import get_optional_user
        user = get_optional_user(request)
        if user and (user.get("role") or "") == "admin":
            return await call_next(request)
        msg = srepo.get("maintenance_message", "") or "سایت موقتاً در دسترس نیست. کمی بعد دوباره امتحان کنید."
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": msg, "maintenance": True},
        )
    except Exception:
        return await call_next(request)

