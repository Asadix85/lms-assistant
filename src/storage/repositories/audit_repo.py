"""لاگ عملیات ادمین."""

from __future__ import annotations

import uuid
from typing import Any

from src.storage.database import Database
from src.web.security import utcnow_iso


class AuditRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def log(
        self,
        *,
        actor_user_id: str,
        action: str,
        target_user_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO admin_audit_log (id, actor_user_id, action, target_user_id, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                actor_user_id,
                action,
                target_user_id,
                detail,
                utcnow_iso(),
            ),
        )
        self.db.connection.commit()

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT a.*, u.lms_username AS actor_username, u.full_name AS actor_name
              FROM admin_audit_log a
              LEFT JOIN users u ON u.id = a.actor_user_id
             ORDER BY a.created_at DESC
             LIMIT ?
            """,
            (limit,),
        )
