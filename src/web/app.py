"""App اصلی FastAPI وب LMS Assistant."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.storage.database import Database
from src.web.session import SessionManager
from src.web.routers import auth, courses, quera, settings as settings_router, sync, proxy

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
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = _prepare_db()
    session = SessionManager(db)
    session.attach_loop(asyncio.get_running_loop())

    app.state.db = db
    app.state.session = session

    # 👇 اضافه کردن lms_assistant برای دسترسی پروکسی
    # (در صورت لاگین موفق، این متغیر در روت auth پر می‌شود)
    app.state.lms_assistant = None

    yield
    db.close()


app = FastAPI(
    title="LMS Assistant Web",
    description="نسخه وب دستیار LMS دانشگاه اصفهان (FastAPI + HTML/CSS)",
    version="0.1.0",
    lifespan=lifespan,
)
from fastapi.middleware.cors import CORSMiddleware

# 👇 اضافه کردن CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در محیط توسعه همه را مجاز می‌کنیم
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === API Routers ===
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api", tags=["lms"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(quera.router, prefix="/api/quera", tags=["quera"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])

# 👇 ثبت روت پروکسی
app.include_router(proxy.router, prefix="/api", tags=["proxy"])

# === Static files ===
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
app.mount("/fonts", StaticFiles(directory=str(ASSETS_DIR / "fonts")), name="fonts")

@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(str(WEB_DIR / "index.html"))

async def keep_lms_session_alive(app: FastAPI):
    """تسک پس‌زمینه برای زنده نگه داشتن نشست LMS."""
    while True:
        try:
            await asyncio.sleep(600)  # هر ۱۰ دقیقه
            
            # 👇 دسترسی به SessionManager از state برنامه
            session_manager = getattr(app.state, "session", None)
            if not session_manager:
                continue
            
            # 👇 دریافت assistant از SessionManager
            try:
                assistant = session_manager.get_assistant()
            except PermissionError:
                # اگر لاگین نشده بود، ادامه بده
                continue

            if assistant and assistant.is_authenticated:
                r = assistant.client.get("/pages/nodemain")
                if "/login" in str(r.url):
                    logger.warning("⚠️ نشست LMS در پس‌زمینه منقضی شد. تلاش برای لاگین مجدد...")
                    creds = session_manager.creds
                    assistant.login(creds.lms_username, creds.lms_password)
                else:
                    logger.debug("💚 نشست LMS در پس‌زمینه زنده است.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"خطا در تسک keep-alive: {e}")