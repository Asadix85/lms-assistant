"""Repository تیکت‌های پشتیبانی."""

from __future__ import annotations

import uuid
from typing import Any

from src.storage.database import Database
from src.web.security import utcnow_iso


class SupportRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_ticket(self, user_id: str, subject: str, body: str) -> dict[str, Any]:
        now = utcnow_iso()
        ticket_id = str(uuid.uuid4())
        msg_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO support_tickets (id, user_id, subject, status, created_at, updated_at)
            VALUES (?, ?, ?, 'open', ?, ?)
            """,
            (ticket_id, user_id, subject.strip(), now, now),
        )
        self.db.execute(
            """
            INSERT INTO support_messages (id, ticket_id, author_user_id, is_staff, body, created_at)
            VALUES (?, ?, ?, 0, ?, ?)
            """,
            (msg_id, ticket_id, user_id, body.strip(), now),
        )
        self.db.connection.commit()
        return self.get_ticket(ticket_id)  # type: ignore[return-value]

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        return self.db.fetch_one(
            "SELECT * FROM support_tickets WHERE id = ?",
            (ticket_id,),
        )

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT t.*,
                   (SELECT COUNT(*) FROM support_messages m WHERE m.ticket_id = t.id) AS message_count
              FROM support_tickets t
             WHERE t.user_id = ?
             ORDER BY t.updated_at DESC
            """,
            (user_id,),
        )

    def list_all(self, status: str | None = None) -> list[dict[str, Any]]:
        if status:
            return self.db.fetch_all(
                """
                SELECT t.*, u.full_name, u.lms_username,
                       (SELECT COUNT(*) FROM support_messages m WHERE m.ticket_id = t.id) AS message_count
                  FROM support_tickets t
                  JOIN users u ON u.id = t.user_id
                 WHERE t.status = ?
                 ORDER BY t.updated_at DESC
                """,
                (status,),
            )
        return self.db.fetch_all(
            """
            SELECT t.*, u.full_name, u.lms_username,
                   (SELECT COUNT(*) FROM support_messages m WHERE m.ticket_id = t.id) AS message_count
              FROM support_tickets t
              JOIN users u ON u.id = t.user_id
             ORDER BY t.updated_at DESC
            """
        )

    def list_messages(self, ticket_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT m.*, u.full_name, u.role
              FROM support_messages m
              JOIN users u ON u.id = m.author_user_id
             WHERE m.ticket_id = ?
             ORDER BY m.created_at ASC
            """,
            (ticket_id,),
        )

    def add_message(
        self,
        ticket_id: str,
        author_user_id: str,
        body: str,
        *,
        is_staff: bool,
    ) -> dict[str, Any]:
        now = utcnow_iso()
        msg_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO support_messages (id, ticket_id, author_user_id, is_staff, body, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (msg_id, ticket_id, author_user_id, 1 if is_staff else 0, body.strip(), now),
        )
        # reopen if user replies to closed? keep status; staff can set
        new_status = None
        if is_staff:
            new_status = "answered"
        else:
            new_status = "open"
        self.db.execute(
            """
            UPDATE support_tickets
               SET updated_at = ?, status = COALESCE(?, status)
             WHERE id = ?
            """,
            (now, new_status, ticket_id),
        )
        self.db.connection.commit()
        return self.db.fetch_one(
            "SELECT * FROM support_messages WHERE id = ?",
            (msg_id,),
        )  # type: ignore[return-value]

    def set_status(self, ticket_id: str, status: str) -> bool:
        if status not in ("open", "answered", "closed"):
            raise ValueError("وضعیت نامعتبر")
        now = utcnow_iso()
        cur = self.db.execute(
            "UPDATE support_tickets SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, ticket_id),
        )
        self.db.connection.commit()
        return (cur.rowcount or 0) > 0
