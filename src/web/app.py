"""App اصلی FastAPI وب LMS Assistant."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config.settings import settings
from src.storage.database import Database
from src.storage.migrations import migrate
from src.web.routers import auth, courses, proxy, quera
from src.web.routers import settings as settings_router
from src.web.routers import sync
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
