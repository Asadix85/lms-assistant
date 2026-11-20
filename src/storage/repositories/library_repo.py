"""Repository کتابخانه عمومی (لینک‌های جزوه و منبع با تایید ادمین)."""

from __future__ import annotations

import uuid
from typing import Any
from urllib.parse import urlparse

from src.storage.database import Database
from src.web.security import utcnow_iso


def _normalize_course_name(name: str) -> str:
    return " ".join(name.strip().split())


def _is_valid_url(url: str) -> bool:
    try:
        p = urlparse(url.strip())
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


class LibraryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------ catalog (library_courses)
    def list_catalog(
        self,
        *,
        term: str | None = None,
        only_with_items: bool = False,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """لیست درس‌های کاتالوگ + تعداد منابع تاییدشده.

        term: اگر داده شود فقط همان ترم؛ None = همه.
        only_with_items: فقط درس‌هایی که حداقل یک منبع approved دارند.
        """
        where = []
        params: list[Any] = []
        if not include_inactive:
            where.append("c.is_active = 1")
        if term:
            where.append("c.term = ?")
            params.append(term.strip())
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        having = "HAVING item_count > 0" if only_with_items else ""
        return self.db.fetch_all(
            f"""
            SELECT c.id,
                   c.name AS course_name,
                   c.code,
                   c.term,
                   c.is_active,
                   c.sort_order,
                   COALESCE(COUNT(i.id), 0) AS item_count,
                   MAX(i.updated_at) AS last_activity
              FROM library_courses c
              LEFT JOIN library_items i
                     ON i.course_name = c.name COLLATE NOCASE
                    AND i.status = 'approved'
             {where_sql}
             GROUP BY c.id
             {having}
             ORDER BY c.sort_order ASC, c.name COLLATE NOCASE
            """,
            tuple(params),
        )

    def get_catalog_course(self, course_id: str) -> dict[str, Any] | None:
        return self.db.fetch_one(
            "SELECT * FROM library_courses WHERE id = ?",
            (course_id,),
        )

    def find_catalog_by_name(self, name: str) -> dict[str, Any] | None:
        name = _normalize_course_name(name)
        return self.db.fetch_one(
            "SELECT * FROM library_courses WHERE name = ? COLLATE NOCASE",
            (name,),
        )

    def create_catalog_course(
        self,
        *,
        name: str,
        code: str = "",
        term: str = "",
        sort_order: int = 0,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        name = _normalize_course_name(name)
        if len(name) < 2:
            raise ValueError("نام درس معتبر نیست")
        existing = self.find_catalog_by_name(name)
        if existing:
            raise ValueError(f"درس «{name}» از قبل در کاتالوگ هست")
        now = utcnow_iso()
        cid = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO library_courses (
                id, name, code, term, is_active, sort_order, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (cid, name, (code or "").strip(), (term or "").strip(), sort_order, created_by, now, now),
        )
        self.db.connection.commit()
        return self.get_catalog_course(cid)  # type: ignore[return-value]

    def bulk_create_catalog(
        self,
        courses: list[dict[str, Any]],
        *,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """اضافه کردن دسته‌ای؛ تکراری‌ها رد می‌شوند."""
        created = 0
        skipped = 0
        errors: list[str] = []
        for i, raw in enumerate(courses):
            name = _normalize_course_name(str(raw.get("name") or ""))
            if len(name) < 2:
                errors.append(f"ردیف {i + 1}: نام نامعتبر")
                continue
            if self.find_catalog_by_name(name):
                skipped += 1
                continue
            try:
                self.create_catalog_course(
                    name=name,
                    code=str(raw.get("code") or ""),
                    term=str(raw.get("term") or ""),
                    sort_order=int(raw.get("sort_order") or 0),
                    created_by=created_by,
                )
                created += 1
            except ValueError as e:
                errors.append(str(e))
        return {"created": created, "skipped": skipped, "errors": errors}

    def update_catalog_course(
        self,
        course_id: str,
        *,
        name: str | None = None,
        code: str | None = None,
        term: str | None = None,
        is_active: bool | None = None,
        sort_order: int | None = None,
    ) -> dict[str, Any] | None:
        row = self.get_catalog_course(course_id)
        if not row:
            return None
        new_name = _normalize_course_name(name) if name is not None else row["name"]
        if name is not None and len(new_name) < 2:
            raise ValueError("نام درس معتبر نیست")
        if name is not None:
            other = self.find_catalog_by_name(new_name)
            if other and other["id"] != course_id:
                raise ValueError("نام درس تکراری است")
            # rename items that matched old name
            if new_name != row["name"]:
                self.db.execute(
                    """
                    UPDATE library_items
                       SET course_name = ?
                     WHERE course_name = ? COLLATE NOCASE
                    """,
                    (new_name, row["name"]),
                )
        now = utcnow_iso()
        self.db.execute(
            """
            UPDATE library_courses
               SET name = ?,
                   code = ?,
                   term = ?,
                   is_active = ?,
                   sort_order = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                new_name,
                (code if code is not None else row["code"]) or "",
                (term if term is not None else row["term"]) or "",
                1 if (is_active if is_active is not None else row["is_active"]) else 0,
                sort_order if sort_order is not None else row["sort_order"],
                now,
                course_id,
            ),
        )
        self.db.connection.commit()
        return self.get_catalog_course(course_id)

    def delete_catalog_course(self, course_id: str) -> bool:
        cur = self.db.execute("DELETE FROM library_courses WHERE id = ?", (course_id,))
        self.db.connection.commit()
        return cur.rowcount > 0

    def list_terms(self) -> list[str]:
        rows = self.db.fetch_all(
            """
            SELECT DISTINCT term FROM library_courses
             WHERE term != '' AND is_active = 1
             ORDER BY term DESC
            """
        )
        return [r["term"] for r in rows]

    def latest_term(self) -> str | None:
        terms = self.list_terms()
        return terms[0] if terms else None

    # ------------------------------------------------------------------ courses (compat alias)
    def list_courses(self, term: str | None = None) -> list[dict[str, Any]]:
        """کاتالوگ فعال؛ اختیاری فیلتر ترم. همیشه همه درس‌های کاتالوگ (حتی بدون منبع)."""
        return self.list_catalog(term=term, only_with_items=False)

    def list_course_names_for_autocomplete(self) -> list[str]:
        rows = self.db.fetch_all(
            """
            SELECT name FROM library_courses
             WHERE is_active = 1
             ORDER BY name COLLATE NOCASE
            """
        )
        names = [r["name"] for r in rows]
        if names:
            return names
        # fallback: names from items if catalog empty
        rows = self.db.fetch_all(
            """
            SELECT DISTINCT course_name AS name
              FROM library_items
             ORDER BY course_name COLLATE NOCASE
            """
        )
        return [r["name"] for r in rows]

    # ------------------------------------------------------------------ items
    def create_item(
        self,
        *,
        course_name: str,
        title: str,
        description: str,
        url: str,
        user_id: str,
    ) -> dict[str, Any]:
        course_name = _normalize_course_name(course_name)
        title = title.strip()
        description = (description or "").strip()
        url = url.strip()

        if not course_name or len(course_name) < 2:
            raise ValueError("نام درس معتبر نیست")
        if not title or len(title) < 2:
            raise ValueError("عنوان معتبر نیست")
        if not _is_valid_url(url):
            raise ValueError("لینک باید با http یا https شروع شود")

        # اگر کاتالوگ پر باشد فقط نام‌های کاتالوگ پذیرفته می‌شوند
        catalog = self.find_catalog_by_name(course_name)
        if catalog:
            course_name = catalog["name"]
        else:
            has_catalog = self.db.fetch_one("SELECT id FROM library_courses LIMIT 1")
            if has_catalog:
                raise ValueError("این درس در کاتالوگ کتابخانه نیست؛ از لیست درس‌ها انتخاب کنید")

        now = utcnow_iso()
        item_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO library_items (
                id, course_name, title, description, url, status,
                submitted_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (item_id, course_name, title, description, url, user_id, now, now),
        )
        self.db.connection.commit()
        return self.get_item(item_id)  # type: ignore[return-value]

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        return self.db.fetch_one(
            """
            SELECT i.*,
                   u.full_name AS submitter_name,
                   u.lms_username AS submitter_username
              FROM library_items i
              LEFT JOIN users u ON u.id = i.submitted_by
             WHERE i.id = ?
            """,
            (item_id,),
        )

    def list_approved_for_course(self, course_name: str) -> list[dict[str, Any]]:
        course_name = _normalize_course_name(course_name)
        return self.db.fetch_all(
            """
            SELECT i.*,
                   u.full_name AS submitter_name
              FROM library_items i
              LEFT JOIN users u ON u.id = i.submitted_by
             WHERE i.course_name = ? AND i.status = 'approved'
             ORDER BY i.avg_rating DESC, i.created_at DESC
            """,
            (course_name,),
        )

    def list_pending(self) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT i.*,
                   u.full_name AS submitter_name,
                   u.lms_username AS submitter_username
              FROM library_items i
              LEFT JOIN users u ON u.id = i.submitted_by
             WHERE i.status = 'pending'
             ORDER BY i.created_at ASC
            """
        )

    def list_my_submissions(self, user_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT * FROM library_items
             WHERE submitted_by = ?
             ORDER BY created_at DESC
            """,
            (user_id,),
        )

    def set_status(
        self,
        item_id: str,
        status: str,
        *,
        admin_user_id: str | None = None,
    ) -> dict[str, Any] | None:
        if status not in ("approved", "rejected", "pending"):
            raise ValueError("وضعیت نامعتبر")
        now = utcnow_iso()
        if status == "approved":
            self.db.execute(
                """
                UPDATE library_items
                   SET status = ?, approved_at = ?, approved_by = ?, updated_at = ?
                 WHERE id = ?
                """,
                (status, now, admin_user_id, now, item_id),
            )
        else:
            self.db.execute(
                """
                UPDATE library_items
                   SET status = ?, approved_at = NULL, approved_by = NULL, updated_at = ?
                 WHERE id = ?
                """,
                (status, now, item_id),
            )
        self.db.connection.commit()
        return self.get_item(item_id)

    def delete_item(self, item_id: str) -> bool:
        cur = self.db.execute("DELETE FROM library_items WHERE id = ?", (item_id,))
        self.db.connection.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ ratings
    def set_rating(self, item_id: str, user_id: str, score: int) -> dict[str, Any]:
        if score < 1 or score > 5:
            raise ValueError("امتیاز باید بین ۱ تا ۵ باشد")
        item = self.get_item(item_id)
        if not item or item["status"] != "approved":
            raise ValueError("آیتم یافت نشد یا هنوز تایید نشده")

        now = utcnow_iso()
        self.db.execute(
            """
            INSERT INTO library_ratings (item_id, user_id, score, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(item_id, user_id) DO UPDATE SET score = excluded.score, created_at = excluded.created_at
            """,
            (item_id, user_id, score, now),
        )
        row = self.db.fetch_one(
            """
            SELECT AVG(score) AS avg_r, COUNT(*) AS cnt
              FROM library_ratings WHERE item_id = ?
            """,
            (item_id,),
        )
        avg_r = float(row["avg_r"] or 0) if row else 0.0
        cnt = int(row["cnt"] or 0) if row else 0
        self.db.execute(
            """
            UPDATE library_items
               SET avg_rating = ?, rating_count = ?, updated_at = ?
             WHERE id = ?
            """,
            (round(avg_r, 2), cnt, now, item_id),
        )
        self.db.connection.commit()
        return self.get_item(item_id)  # type: ignore[return-value]

    def get_user_rating(self, item_id: str, user_id: str) -> int | None:
        row = self.db.fetch_one(
            "SELECT score FROM library_ratings WHERE item_id = ? AND user_id = ?",
            (item_id, user_id),
        )
        return int(row["score"]) if row else None

    # ------------------------------------------------------------------ comments
    def add_comment(self, item_id: str, user_id: str, body: str) -> dict[str, Any]:
        body = body.strip()
        if len(body) < 1 or len(body) > 2000:
            raise ValueError("متن نظر نامعتبر است")
        item = self.get_item(item_id)
        if not item or item["status"] != "approved":
            raise ValueError("آیتم یافت نشد یا هنوز تایید نشده")

        now = utcnow_iso()
        cid = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO library_comments (id, item_id, user_id, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cid, item_id, user_id, body, now),
        )
        self.db.connection.commit()
        return self.db.fetch_one(
            """
            SELECT c.*, u.full_name AS author_name
              FROM library_comments c
              LEFT JOIN users u ON u.id = c.user_id
             WHERE c.id = ?
            """,
            (cid,),
        )  # type: ignore[return-value]

    def list_comments(self, item_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT c.*, u.full_name AS author_name
              FROM library_comments c
              LEFT JOIN users u ON u.id = c.user_id
             WHERE c.item_id = ?
             ORDER BY c.created_at ASC
            """,
            (item_id,),
        )

    # ------------------------------------------------------------------ reports
    def report_item(self, item_id: str, user_id: str, reason: str = "") -> dict[str, Any]:
        item = self.get_item(item_id)
        if not item:
            raise ValueError("آیتم یافت نشد")
        existing = self.db.fetch_one(
            """
            SELECT id FROM library_reports
             WHERE item_id = ? AND user_id = ? AND resolved = 0
            """,
            (item_id, user_id),
        )
        if existing:
            raise ValueError("قبلاً این مورد را گزارش کرده‌اید")

        now = utcnow_iso()
        rid = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO library_reports (id, item_id, user_id, reason, created_at, resolved)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (rid, item_id, user_id, (reason or "").strip()[:500], now),
        )
        self.db.execute(
            """
            UPDATE library_items
               SET report_count = report_count + 1, updated_at = ?
             WHERE id = ?
            """,
            (now, item_id),
        )
        self.db.connection.commit()
        return self.get_item(item_id)  # type: ignore[return-value]

    def list_open_reports(self) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT r.*,
                   i.title AS item_title,
                   i.url AS item_url,
                   i.course_name,
                   i.status AS item_status,
                   u.full_name AS reporter_name,
                   u.lms_username AS reporter_username
              FROM library_reports r
              JOIN library_items i ON i.id = r.item_id
              LEFT JOIN users u ON u.id = r.user_id
             WHERE r.resolved = 0
             ORDER BY r.created_at ASC
            """
        )

    def resolve_report(self, report_id: str) -> bool:
        cur = self.db.execute(
            "UPDATE library_reports SET resolved = 1 WHERE id = ?",
            (report_id,),
        )
        self.db.connection.commit()
        return cur.rowcount > 0
