#!/usr/bin/env python
"""LMS Assistant CLI."""

import os
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.services.lms_assistant import LMSAssistant
from src.services.sync_service import SyncService
from src.storage.database import Database
from src.storage.repositories import (
    ContentRepository,
    CourseRepository,
    EventRepository,
    SettingRepository,
)

# === Setup ===
load_dotenv()

app = typer.Typer(
    name="lms-assistant",
    help="🎓 دستیار LMS دانشگاه اصفهان",
    no_args_is_help=True,
)

console = Console()

DB_PATH = Path("data/lms.db")


# === Helpers ===


def get_db() -> Database:
    """اتصال به دیتابیس."""
    db = Database(DB_PATH)
    db.connect()
    if not DB_PATH.exists() or not _has_tables(db):
        db.init_schema()
    return db


def _has_tables(db: Database) -> bool:
    """بررسی وجود جداول."""
    try:
        result = db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='courses'"
        )
        return result is not None
    except Exception:
        return False


def ensure_login() -> LMSAssistant:
    """Login به LMS."""
    username = os.environ.get("LMS_USERNAME")
    password = os.environ.get("LMS_PASSWORD")

    if not username or not password:
        console.print("[red]❌ متغیرهای LMS_USERNAME و LMS_PASSWORD در .env نیستند[/red]")
        raise typer.Exit(1)

    assistant = LMSAssistant(username=username, password=password)

    with console.status("[bold cyan]🔐 ورود به LMS..."):
        if not assistant.login():
            console.print("[red]❌ ورود ناموفق[/red]")
            raise typer.Exit(1)

    console.print(f"[green]✅ وارد شد (User ID: {assistant.user_id})[/green]")
    return assistant


# === Commands ===


@app.command()
def update(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="نمایش جزئیات"),
) -> None:
    """🔄 بروزرسانی از LMS."""
    console.print(Panel.fit("🔄 بروزرسانی از LMS", style="bold cyan"))

    db = get_db()
    assistant = ensure_login()

    try:
        sync = SyncService(assistant, db)

        with console.status("[bold yellow]⏳ در حال Sync..."):
            result = sync.sync()

        if result.has_error:
            console.print(f"[red]❌ خطا: {result.error}[/red]")
            raise typer.Exit(1)

        # خلاصه
        console.print()

        if result.is_first_sync:
            console.print(Panel(
                f"[bold green]🎉 اولین Sync موفق![/bold green]\n\n"
                f"📚 {result.courses_new} درس\n"
                f"📄 {result.contents_new} فایل\n"
                f"📅 {result.events_new} رویداد\n\n"
                f"⏱️  {result.duration_seconds:.1f} ثانیه",
                title="نتیجه",
                style="green",
            ))
        elif result.total_new == 0:
            console.print(Panel(
                "[bold]✨ هیچ تغییر جدیدی نیست[/bold]",
                title="نتیجه",
                style="blue",
            ))
        else:
            table = Table(title="📢 تغییرات جدید", show_header=True)
            table.add_column("نوع", style="cyan")
            table.add_column("تعداد", style="yellow")

            if result.courses_new:
                table.add_row("📚 درس", str(result.courses_new))
            if result.contents_new:
                table.add_row("📄 فایل", str(result.contents_new))
            if result.events_new:
                table.add_row("📅 رویداد", str(result.events_new))

            console.print(table)

        console.print(f"\n[dim]⏱️  {result.duration_seconds:.1f} ثانیه[/dim]")

        if verbose:
            console.print("\n[bold]📋 تغییرات:[/bold]")
            for change in result.changes[:20]:
                console.print(f"  • {change.type.value}: {change.entity_type.value} ({change.entity_id})")

    finally:
        assistant.close()
        db.close()


@app.command()
def courses(
    domain: str = typer.Option(None, "--domain", "-d", help="فیلتر دامنه (lms3/lms4/lms5)"),
    active_only: bool = typer.Option(False, "--active", "-a", help="فقط دروس فعال"),
) -> None:
    """📚 نمایش دروس."""
    db = get_db()
    repo = CourseRepository(db)

    if active_only:
        items = repo.get_active()
    elif domain:
        items = repo.get_by_domain(domain)
    else:
        items = repo.get_all()

    if not items:
        console.print("[yellow]⚠️ هیچ درسی در دیتابیس نیست. اول `update` بزن.[/yellow]")
        db.close()
        return

    table = Table(title=f"📚 دروس ({len(items)})", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("نام", style="white")
    table.add_column("استاد", style="green")
    table.add_column("کد", style="yellow")
    table.add_column("دامنه", style="magenta")
    table.add_column("وضعیت", style="cyan")

    for i, c in enumerate(items, 1):
        domain_icon = {"lms3": "🟢", "lms4": "🔵", "lms5": "🔴"}.get(c.domain, "⚪")
        status = "✓" if c.is_active else "✗"
        table.add_row(
            str(i),
            c.name,
            c.teacher or "—",
            c.code or "—",
            f"{domain_icon} {c.domain}",
            status,
        )

    console.print(table)
    db.close()


@app.command()
def contents(
    course: str = typer.Option(None, "--course", "-c", help="فیلتر با شناسه درس"),
) -> None:
    """📄 نمایش فایل‌ها."""
    db = get_db()
    repo = ContentRepository(db)

    if course:
        items = repo.get_by_course(course)
    else:
        items = repo.get_all()

    if not items:
        console.print("[yellow]⚠️ هیچ فایلی در دیتابیس نیست.[/yellow]")
        db.close()
        return

    table = Table(title=f"📄 فایل‌ها ({len(items)})", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("عنوان", style="white")
    table.add_column("نوع", style="yellow")
    table.add_column("درس", style="cyan")

    # map course_id → name
    course_repo = CourseRepository(db)
    course_names = {c.id: c.name for c in course_repo.get_all()}

    for i, c in enumerate(items, 1):
        table.add_row(
            str(i),
            c.title,
            c.content_type,
            course_names.get(c.course_id, c.course_id),
        )

    console.print(table)
    db.close()


@app.command()
def events(
    upcoming: bool = typer.Option(False, "--upcoming", "-u", help="فقط رویدادهای آینده"),
    limit: int = typer.Option(20, "--limit", "-n", help="حداکثر تعداد"),
) -> None:
    """📅 نمایش رویدادها (جلسات آنلاین)."""
    db = get_db()
    repo = EventRepository(db)

    if upcoming:
        items = repo.get_upcoming(limit=limit)
    else:
        items = repo.get_all()[:limit]

    if not items:
        console.print("[yellow]⚠️ هیچ رویدادی در دیتابیس نیست.[/yellow]")
        db.close()
        return

    table = Table(title=f"📅 رویدادها ({len(items)})", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("عنوان", style="white")
    table.add_column("ساعت", style="green")
    table.add_column("لینک", style="cyan")

    for i, e in enumerate(items, 1):
        time_str = e.start_at.strftime("%H:%M") if e.start_at else "—"
        url_short = (e.url[:40] + "...") if e.url and len(e.url) > 40 else (e.url or "—")
        table.add_row(str(i), e.title, time_str, url_short)

    console.print(table)
    db.close()


@app.command()
def changes(
    limit: int = typer.Option(20, "--limit", "-n", help="حداکثر تعداد"),
) -> None:
    """🔔 نمایش تغییرات اخیر."""
    db = get_db()

    rows = db.fetch_all(
        "SELECT * FROM changes ORDER BY detected_at DESC LIMIT ?",
        (limit,),
    )

    if not rows:
        console.print("[yellow]⚠️ هیچ تغییری ثبت نشده.[/yellow]")
        db.close()
        return

    table = Table(title=f"🔔 تغییرات اخیر", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("نوع", style="yellow")
    table.add_column("موجودیت", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("زمان", style="green")

    for i, r in enumerate(rows, 1):
        table.add_row(
            str(i),
            r["type"],
            r["entity_type"],
            r["entity_id"][:20],
            r["detected_at"][:19],
        )

    console.print(table)
    db.close()


@app.command()
def status() -> None:
    """📊 وضعیت کلی."""
    db = get_db()

    course_repo = CourseRepository(db)
    content_repo = ContentRepository(db)
    event_repo = EventRepository(db)
    setting_repo = SettingRepository(db)

    last_sync = setting_repo.get("last_sync_at", "—")
    first_sync = setting_repo.get("first_sync_done", "false")

    console.print(Panel.fit(
        f"[bold cyan]📊 وضعیت LMS Assistant[/bold cyan]\n\n"
        f"📚 دروس:       [yellow]{course_repo.count()}[/yellow]\n"
        f"📄 فایل‌ها:     [yellow]{content_repo.count()}[/yellow]\n"
        f"📅 رویدادها:   [yellow]{event_repo.count()}[/yellow]\n\n"
        f"🔄 آخرین Sync: [green]{last_sync[:19] if last_sync != '—' else '—'}[/green]\n"
        f"🎉 اولین Sync: [green]{'✅' if first_sync == 'true' else '❌'}[/green]",
        title="وضعیت",
        style="cyan",
    ))

    db.close()


# === Entry Point ===


if __name__ == "__main__":
    app()