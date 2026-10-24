"""App اصلی FastAPI وب LMS Assistant."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.storage.database import Database
from src.web.session import SessionManager

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"


def _prepare_db() -> Database:
    """ساخت/بازکردن دیتابیس و مقداردهی schema در صورت نیاز."""
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
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = _prepare_db()
    session = SessionManager(db)
    session.attach_loop(asyncio.get_running_loop())
    app.state.db = db
    app.state.session = session
    yield
    db.close()


app = FastAPI(
    title="LMS Assistant Web",
    description="نسخه وب دستیار LMS دانشگاه اصفهان (FastAPI + HTML/CSS)",
    version="0.1.0",
    lifespan=lifespan,
)

# === API Routers ===
from src.web.routers import auth, courses, quera, settings as settings_router, sync  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api", tags=["lms"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(quera.router, prefix="/api/quera", tags=["quera"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])

# === Static files (HTML/CSS/JS فرانت‌اند) ===
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

# === فونت‌های خودمیزبان (Vazirmatn) ===
app.mount("/fonts", StaticFiles(directory=str(ASSETS_DIR / "fonts")), name="fonts")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(str(WEB_DIR / "index.html"))
