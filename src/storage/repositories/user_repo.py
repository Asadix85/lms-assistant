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
                   SET full_name = COALESCE(?, full_name),
                       lms_user_id = COALESCE(?, lms_user_id),
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
            INSERT INTO users (id, lms_username, lms_user_id, full_name, role, is_active, created_at, last_login_at)
            VALUES (?, ?, ?, ?, 'user', 1, ?, ?)
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
        lms_cookies_json: str | None = None,
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
        cookies_enc = (
            encrypt_secret(lms_cookies_json)
            if lms_cookies_json is not None
            else (row["lms_cookies_enc"] if row and "lms_cookies_enc" in row.keys() else None)
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
                   SET lms_password_enc = ?,
                       lms_cookies_enc = ?,
                       quera_username = ?,
                       quera_password_enc = ?,
                       updated_at = ?
                 WHERE user_id = ?
                """,
                (lms_enc, cookies_enc, q_user, q_enc, now, user_id),
            )
        else:
            self.db.execute(
                """
                INSERT INTO user_secrets
                    (user_id, lms_password_enc, lms_cookies_enc,
                     quera_username, quera_password_enc, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, lms_enc, cookies_enc, q_user, q_enc, now),
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
                "lms_cookies_json": "",
                "quera_username": "",
                "quera_password": "",
            }
        cookies_raw = ""
        if "lms_cookies_enc" in row.keys() and row["lms_cookies_enc"]:
            try:
                cookies_raw = decrypt_secret(row["lms_cookies_enc"])
            except ValueError:
                cookies_raw = ""
        return {
            "lms_password": decrypt_secret(row["lms_password_enc"] or ""),
            "lms_cookies_json": cookies_raw,
            "quera_username": row["quera_username"] or "",
            "quera_password": decrypt_secret(row["quera_password_enc"] or ""),
        }

    def clear_lms_password(self, user_id: str) -> None:
        self.db.execute(
            "UPDATE user_secrets SET lms_password_enc = NULL, updated_at = ? WHERE user_id = ?",
            (utcnow_iso(), user_id),
        )
        self.db.connection.commit()

    def clear_lms_cookies(self, user_id: str) -> None:
        self.db.execute(
            "UPDATE user_secrets SET lms_cookies_enc = NULL, updated_at = ? WHERE user_id = ?",
            (utcnow_iso(), user_id),
        )
        self.db.connection.commit()

    def delete_expired_sessions(self) -> int:
        """حذف sessionهای منقضی؛ تعداد حذف‌شده را برمی‌گرداند."""
        now = utcnow_iso()
        cur = self.db.execute(
            "DELETE FROM web_sessions WHERE expires_at < ?",
            (now,),
        )
        self.db.connection.commit()
        return cur.rowcount if cur is not None else 0

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

    # --- admin ---

    def list_users(self) -> list[dict]:
        rows = self.db.fetch_all(
            """
            SELECT u.id, u.lms_username, u.lms_user_id, u.full_name, u.role,
                   COALESCE(u.is_active, 1) AS is_active,
                   u.created_at, u.last_login_at,
                   (SELECT COUNT(*) FROM web_sessions s WHERE s.user_id = u.id) AS session_count
              FROM users u
             ORDER BY u.last_login_at DESC, u.created_at DESC
            """
        )
        # SQLite ignores NULLS LAST on older versions — fallback sort in Python if needed
        return rows or []

    def set_role(self, user_id: str, role: str) -> bool:
        if role not in ("user", "admin"):
            raise ValueError("نقش نامعتبر")
        if role == "admin":
            from src.web.security import MAX_ADMINS
            current = self.get_by_id(user_id)
            if not current or (current.get("role") or "user") != "admin":
                if self.count_admins() >= MAX_ADMINS:
                    raise ValueError(f"حداکثر {MAX_ADMINS} ادمین مجاز است")
        cur = self.db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (role, user_id),
        )
        self.db.connection.commit()
        return (cur.rowcount or 0) > 0

    def set_active(self, user_id: str, active: bool) -> bool:
        cur = self.db.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if active else 0, user_id),
        )
        self.db.connection.commit()
        return (cur.rowcount or 0) > 0

    def count_users(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) AS n FROM users")
        return int(row["n"]) if row else 0

    def count_admins(self) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin'"
        )
        return int(row["n"]) if row else 0

    def create_local_admin(
        self,
        *,
        username: str,
        password_hash: str,
        full_name: str = "مدیر سیستم",
    ) -> dict:
        """ساخت ادمین محلی (بدون LMS)."""
        now = utcnow_iso()
        user_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO users (
                id, lms_username, lms_user_id, full_name, role, is_active,
                password_hash, auth_provider, created_at, last_login_at
            ) VALUES (?, ?, NULL, ?, 'admin', 1, ?, 'local', ?, ?)
            """,
            (user_id, username, full_name, password_hash, now, now),
        )
        self.db.connection.commit()
        return self.get_by_id(user_id)  # type: ignore[return-value]

    def get_by_local_username(self, username: str) -> dict | None:
        return self.db.fetch_one(
            "SELECT * FROM users WHERE lms_username = ? AND auth_provider = 'local'",
            (username,),
        )

    def touch_last_login(self, user_id: str) -> None:
        self.db.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (utcnow_iso(), user_id),
        )
        self.db.connection.commit()

