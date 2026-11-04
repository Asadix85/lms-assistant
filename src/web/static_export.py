"""ساخت باندل JSON استاتیک از دیتابیس + رمزنگاری برای GitHub Pages.

این ماژول وابستگی به FastAPI ندارد تا در GitHub Actions بدون نصب وب‌سرور
قابل استفاده باشد. خروجی آن دقیقاً همان شکل پاسخ‌های API وب است، بنابراین
فرانت‌اند استاتیک بدون تغییر در رندر، داده‌ها را از باندل می‌خواند.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
from datetime import datetime, timedelta # 👈 timedelta اضافه شد
from pathlib import Path

from loguru import logger

from src.storage.database import Database
from src.storage.repositories import (
    AssignmentRepository,
    ChangeRepository,
    ContentRepository,
    CourseRepository,
    EventRepository,
    MemberRepository,
    PostRepository,
    QueraAssignmentRepository,
    QueraCourseRepository,
    SettingRepository,
)
from src.web.schemas import (
    AssignmentOut,
    ChangeOut,
    ContentOut,
    CourseOut,
    EventOut,
    MemberOut,
    PostOut,
    QueraAssignmentOut,
    QueraCourseOut,
)

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"

# همان نگاشت Router تنظیمات وب (بدون import از fastapi)
SYNC_KEYS = {
    "courses": "sync_courses",
    "contents": "sync_contents",
    "events": "sync_events",
    "wall": "sync_wall",
    "members": "sync_members",
}


def _repos(db: Database, user_id: str) -> dict:
    return {
        "courses": CourseRepository(db, user_id),
        "contents": ContentRepository(db, user_id),
        "events": EventRepository(db, user_id),
        "posts": PostRepository(db, user_id),
        "assignments": AssignmentRepository(db, user_id),
        "members": MemberRepository(db, user_id),
        "changes": ChangeRepository(db, user_id),
    }


def build_dashboard(db: Database, user_id: str) -> dict:
    """همان ساختار GET /api/dashboard — بین روتر وب و اکسپورت استاتیک مشترک."""
    r = _repos(db, user_id)
    upcoming_events = r["events"].get_upcoming(limit=8)
    upcoming_assignments = r["assignments"].get_upcoming(limit=8)
    recent_posts = r["posts"].get_all()[:8]
    recent_changes = r["changes"].get_recent(limit=10)

    # 👇 استخراج رویدادهای امروز (جلسات آنلاین و غیره)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    today_events = []
    for e in upcoming_events:
        if e.start_at and today_start <= e.start_at < today_end:
            today_events.append(EventOut.from_model(e))

    return {
        "stats": {
            "courses": r["courses"].count(),
            "active_courses": len(r["courses"].get_active()),
            "contents": r["contents"].count(),
            "events": r["events"].count(),
            "posts": r["posts"].count(),
            "assignments": r["assignments"].count(),
            "pending_assignments": sum(
                1 for a in r["assignments"].get_all() if not a.is_done
            ),
        },
        "upcoming_events": [EventOut.from_model(e) for e in upcoming_events],
        "upcoming_assignments": [
            AssignmentOut.from_model(a) for a in upcoming_assignments
        ],
        "recent_posts": [PostOut.from_model(p) for p in recent_posts],
        "recent_changes": [ChangeOut.from_model(c) for c in recent_changes],
        "today_events": today_events, # 👈 اضافه شد
    }


def build_bundle(
    db: Database,
    *,
    user_id: str = "__local__",
    full_name: str | None = None,
    username: str | None = None,
    source: str = "db",
    generated_at: str | None = None,
) -> dict:
    """باندل کامل داده برای سایت استاتیک (هم‌شکل پاسخ‌های API)."""
    r = _repos(db, user_id)
    try:
        quera_assignments = [
            QueraAssignmentOut.from_model(a)
            for a in QueraAssignmentRepository(db, user_id).get_all()
        ]
    except Exception:
        quera_assignments = []
    try:
        quera_courses = [
            QueraCourseOut.from_model(c) for c in QueraCourseRepository(db, user_id).get_all()
        ]
    except Exception:
        quera_courses = []

    try:
        setting_repo = SettingRepository(db, user_id)
        sync_settings = {
            ui_key: setting_repo.get(db_key, "true") == "true"
            for ui_key, db_key in SYNC_KEYS.items()
        }
    except Exception:
        sync_settings = {}

    return {
        "v": 1,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "source": source,  # "live" = سینک زنده در Actions | "db" = آخرین دیتابیس کامیت‌شده
        "auth": {
            "full_name": full_name,
            "username": username,
            "lms_logged_in": bool(username),
        },
        "dashboard": build_dashboard(db, user_id),
        "courses": [CourseOut.from_model(c) for c in r["courses"].get_all()],
        "contents": [ContentOut.from_model(c) for c in r["contents"].get_all()],
        "events": [EventOut.from_model(e) for e in r["events"].get_all()],
        "posts": [PostOut.from_model(p) for p in r["posts"].get_all()],
        "assignments": [AssignmentOut.from_model(a) for a in r["assignments"].get_all()],
        "members": [MemberOut.from_model(m) for m in r["members"].get_all()],
        "changes": [ChangeOut.from_model(c) for c in r["changes"].get_recent(limit=100)],
        "quera_assignments": quera_assignments,
        "quera_courses": quera_courses,
        "sync_settings": sync_settings,
    }


# === رمزنگاری AES-256-GCM (کلید از PBKDF2-SHA256) ===

PBKDF2_ITERATIONS = 150_000


def encrypt_payload(payload: bytes, passphrase: str) -> dict:
    """رمزنگاری باندل با AES-256-GCM. خروجی یک JSON ساده‌ی base64."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    iv = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(iv, payload, None)
    return {
        "enc": True,
        "v": 1,
        "kdf": "pbkdf2-sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "data": base64.b64encode(ciphertext).decode("ascii"),
    }


# === نوشتن سایت ===


def write_site(
    bundle: dict,
    out_dir: str | Path,
    passphrase: str | None = None,
    cname: str | None = None,
) -> Path:
    """کپی web/ به پوشه خروجی + باندل داده (+ رمزنگاری اختیاری) + CNAME."""
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(WEB_DIR, out)

    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, ensure_ascii=False).encode("utf-8")

    if passphrase:
        envelope = encrypt_payload(payload, passphrase)
        (data_dir / "bundle.json").write_text(
            json.dumps(envelope, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("🔐 باندل با AES-256-GCM رمزنگاری شد")
    else:
        (data_dir / "bundle.json").write_text(
            payload.decode("utf-8"), encoding="utf-8"
        )
        logger.warning(
            "⚠️ باندل بدون رمزنگاری ساخته شد — محتوا برای هر بازدیدکننده قابل مشاهده است"
        )

    # گیتهاب Pages: بدون Jekyll + جلوگیری از ایندکس داده‌ها
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text(
        "User-agent: *\nDisallow: /data/\n", encoding="utf-8"
    )

    if cname:
        (out / "CNAME").write_text(cname.strip() + "\n", encoding="utf-8")

    logger.info(f"✅ سایت استاتیک ساخته شد: {out.resolve()}")
    return out