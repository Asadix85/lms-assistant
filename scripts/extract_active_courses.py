#!/usr/bin/env python3
"""استخراج دروس فعال LMS برای کاتالوگ کتابخانه.

منبع credentials: CredentialProvider (keyring → .env fallback)
نه .env خام.

اجرا:
  python scripts/extract_active_courses.py
  python scripts/extract_active_courses.py --json-only > data/active_courses_export.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.services.credential_provider import CredentialProvider
from src.services.lms_assistant import LMSAssistant

console = Console()


def main() -> int:
    load_dotenv(ROOT / ".env")  # فقط برای fallback داخل CredentialProvider

    json_only = "--json-only" in sys.argv

    creds = CredentialProvider.load()
    if not creds.lms_username or not creds.lms_password:
        console.print(
            "[red]Credentials LMS پیدا نشد.[/red]\n"
            "[dim]یک‌بار از GUI لاگین کن (keyring پر می‌شود)،\n"
            "یا LMS_USERNAME / LMS_PASSWORD را در .env بگذار.[/dim]"
        )
        return 1

    assistant = LMSAssistant(
        username=creds.lms_username,
        password=creds.lms_password,
    )

    try:
        if not json_only:
            with console.status("[bold cyan]ورود به LMS..."):
                ok = assistant.login()
        else:
            ok = assistant.login()

        if not ok:
            console.print("[red]ورود ناموفق — username/password را چک کن[/red]")
            return 1

        if not json_only:
            console.print(
                f"[green]وارد شد — user_id={assistant.user_id}[/green]"
            )
            with console.status("[bold yellow]دریافت دروس فعال..."):
                courses = assistant.get_active_courses()
        else:
            courses = assistant.get_active_courses()

        courses = sorted(courses, key=lambda c: (c.term or "", c.name or ""))

        payload = [
            {
                "name": c.name,
                "code": c.code or "",
                "term": c.term or "",
                "id": c.id,
                "domain": c.domain,
                "teacher": c.teacher or "",
                "url": c.url,
            }
            for c in courses
        ]

        if json_only:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        table = Table(
            title=f"دروس فعال ({len(payload)})",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("نام", style="white")
        table.add_column("کد", style="yellow")
        table.add_column("ترم", style="green")
        table.add_column("استاد", style="magenta")
        table.add_column("دامنه", style="cyan")
        table.add_column("group_id", style="dim")

        missing_code = 0
        for i, row in enumerate(payload, 1):
            if not row["code"]:
                missing_code += 1
            table.add_row(
                str(i),
                row["name"],
                row["code"] or "—",
                row["term"] or "—",
                row["teacher"] or "—",
                row["domain"],
                row["id"],
            )

        console.print(table)
        console.print()
        console.print(f"[bold]جمع:[/bold] {len(payload)} درس فعال")
        if missing_code:
            console.print(
                f"[yellow]⚠ {missing_code} درس بدون کد — "
                "بعداً parser یا ورود دستی[/yellow]"
            )

        out_path = ROOT / "data" / "active_courses_export.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.print(f"\n[green]JSON:[/green] {out_path}")
        console.print("[dim]همین فایل را بفرست.[/dim]")
        return 0

    finally:
        assistant.close()


if __name__ == "__main__":
    raise SystemExit(main())