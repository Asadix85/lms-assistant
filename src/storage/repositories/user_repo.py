"""Repository کاربران، session وب، و اسرار رمزنگاری‌شده."""

from __future__ import annotations

import uuid
from typing import Any

from src.storage.database import Database
from src.web.security import (
    decrypt_secret,
    encrypt_secret,
    expires_in_days,
    hash_token,
    parse_iso,
    utcnow_iso,
)


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --- users ---

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def get_by_lms_username(self, lms_username: str) -> dict[str, Any] | None:
        return self.db.fetch_one(
            "SELECT * FROM users WHERE lms_username = ?",
            (lms_username,),
        )

    def upsert_from_lms_login(
            self,
            *,
            lms_username: str,
            full_name: str | None,
            lms_user_id: str | None,
    ) -> dict[str, Any]:
        now = utcnow_iso()
        existing = self.get_by_lms_username(lms_username)
        if existing:
            self.db.execute(
                """
                UPDATE users
                SET full_name     = COALESCE(?, full_name),
                    lms_user_id   = COALESCE(?, lms_user_id),
                    last_login_at = ?
                WHERE id = ?
                """,
                (full_name, lms_user_id, now, existing["id"]),
            )
            self.db.connection.commit()
            return self.get_by_id(existing["id"])  # type: ignore[return-value]

        user_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO users (id, lms_username, lms_user_id, full_name, role, created_at, last_login_at)
            VALUES (?, ?, ?, ?, 'user', ?, ?)
            """,
            (user_id, lms_username, lms_user_id, full_name, now, now),
        )
        self.db.connection.commit()
        return self.get_by_id(user_id)  # type: ignore[return-value]

    # --- secrets ---

    def save_secrets(
            self,
            user_id: str,
            *,
            lms_password: str | None = None,
            quera_username: str | None = None,
            quera_password: str | None = None,
    ) -> None:
        now = utcnow_iso()
        row = self.db.fetch_one(
            "SELECT * FROM user_secrets WHERE user_id = ?",
            (user_id,),
        )
        lms_enc = (
            encrypt_secret(lms_password)
            if lms_password is not None
            else (row["lms_password_enc"] if row else None)
        )
        q_user = (
            quera_username
            if quera_username is not None
            else (row["quera_username"] if row else None)
        )
        q_enc = (
            encrypt_secret(quera_password)
            if quera_password is not None
            else (row["quera_password_enc"] if row else None)
        )

        if row:
            self.db.execute(
                """
                UPDATE user_secrets
                SET lms_password_enc   = ?,
                    quera_username     = ?,
                    quera_password_enc = ?,
                    updated_at         = ?
                WHERE user_id = ?
                """,
                (lms_enc, q_user, q_enc, now, user_id),
            )
        else:
            self.db.execute(
                """
                INSERT INTO user_secrets
                (user_id, lms_password_enc, quera_username, quera_password_enc, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, lms_enc, q_user, q_enc, now),
            )
        self.db.connection.commit()

    def load_secrets(self, user_id: str) -> dict[str, str]:
        row = self.db.fetch_one(
            "SELECT * FROM user_secrets WHERE user_id = ?",
            (user_id,),
        )
        if not row:
            return {
                "lms_password": "",
                "quera_username": "",
                "quera_password": "",
            }
        return {
            "lms_password": decrypt_secret(row["lms_password_enc"] or ""),
            "quera_username": row["quera_username"] or "",
            "quera_password": decrypt_secret(row["quera_password_enc"] or ""),
        }

    def clear_lms_password(self, user_id: str) -> None:
        self.db.execute(
            "UPDATE user_secrets SET lms_password_enc = NULL, updated_at = ? WHERE user_id = ?",
            (utcnow_iso(), user_id),
        )
        self.db.connection.commit()

    # --- web sessions ---

    def create_session(
            self,
            user_id: str,
            raw_token: str,
            *,
            user_agent: str | None = None,
            days: int = 30,
    ) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = utcnow_iso()
        exp = expires_in_days(days)
        self.db.execute(
            """
            INSERT INTO web_sessions (id, user_id, token_hash, expires_at, created_at, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, user_id, hash_token(raw_token), exp, now, user_agent),
        )
        self.db.connection.commit()
        return {
            "id": session_id,
            "user_id": user_id,
            "expires_at": exp,
        }

    def get_user_by_token(self, raw_token: str) -> dict[str, Any] | None:
        if not raw_token:
            return None
        row = self.db.fetch_one(
            """
            SELECT s.id AS session_id, s.expires_at, u.*
            FROM web_sessions s
                     JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (hash_token(raw_token),),
        )
        if not row:
            return None
        try:
            if parse_iso(row["expires_at"]) < parse_iso(utcnow_iso()):
                self.delete_session_by_id(row["session_id"])
                return None
        except ValueError:
            return None
        return row

    def delete_session_by_token(self, raw_token: str) -> None:
        if not raw_token:
            return
        self.db.execute(
            "DELETE FROM web_sessions WHERE token_hash = ?",
            (hash_token(raw_token),),
        )
        self.db.connection.commit()

    def delete_session_by_id(self, session_id: str) -> None:
        self.db.execute("DELETE FROM web_sessions WHERE id = ?", (session_id,))
        self.db.connection.commit()

    def delete_user_sessions(self, user_id: str) -> None:
        self.db.execute("DELETE FROM web_sessions WHERE user_id = ?", (user_id,))
        self.db.connection.commit()
