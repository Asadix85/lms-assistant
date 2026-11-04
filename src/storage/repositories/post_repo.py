"""Repository برای Post (scoped به user_id)."""

from datetime import datetime

from loguru import logger

from src.models.post import Post
from src.storage.repositories.base import BaseRepository


class PostRepository(BaseRepository):
    TABLE_NAME = "posts"

    def save(self, post: Post) -> None:
        data = self._to_dict(post)
        existing = self.db.fetch_one(
            "SELECT id FROM posts WHERE user_id = ? AND id = ?",
            (self.user_id, post.id),
        )

        if existing:
            self.db.execute(
                """
                UPDATE posts SET
                    text = ?, posted_at = ?, last_seen_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (
                    data["text"], data["posted_at"], data["last_seen_at"],
                    self.user_id, data["id"],
                ),
            )
        else:
            self.db.execute(
                """
                INSERT INTO posts (
                    user_id, id, course_id, author, author_id, text,
                    posted_at, posted_at_jalali, post_url,
                    is_new, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    data["id"], data["course_id"], data["author"],
                    data["author_id"], data["text"], data["posted_at"],
                    data["posted_at_jalali"], data["post_url"],
                    data["is_new"], data["first_seen_at"], data["last_seen_at"],
                ),
            )
            logger.debug(f"درج پست جدید از {post.author}")

        self.db.connection.commit()

    def get_by_id(self, post_id: str) -> Post | None:
        row = self.db.fetch_one(
            "SELECT * FROM posts WHERE user_id = ? AND id = ?",
            (self.user_id, post_id),
        )
        return self._from_dict(row) if row else None

    def get_all(self) -> list[Post]:
        rows = self.db.fetch_all(
            "SELECT * FROM posts WHERE user_id = ? ORDER BY posted_at DESC",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def get_by_course(self, course_id: str, limit: int = 50) -> list[Post]:
        rows = self.db.fetch_all(
            "SELECT * FROM posts WHERE user_id = ? AND course_id = ? "
            "ORDER BY posted_at DESC LIMIT ?",
            (self.user_id, course_id, limit),
        )
        return [self._from_dict(r) for r in rows]

    def get_new(self) -> list[Post]:
        rows = self.db.fetch_all(
            "SELECT * FROM posts WHERE user_id = ? AND is_new = 1 ORDER BY posted_at DESC",
            (self.user_id,),
        )
        return [self._from_dict(r) for r in rows]

    def mark_all_seen(self) -> None:
        self.db.execute(
            "UPDATE posts SET is_new = 0 WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.connection.commit()

    def _to_dict(self, p: Post) -> dict:
        return {
            "id": p.id,
            "course_id": p.course_id,
            "author": p.author,
            "author_id": p.author_id,
            "text": p.text,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "posted_at_jalali": p.posted_at_jalali,
            "post_url": p.post_url,
            "is_new": 1 if p.is_new else 0,
            "first_seen_at": p.first_seen_at.isoformat(),
            "last_seen_at": p.last_seen_at.isoformat(),
        }

    def _from_dict(self, row: dict) -> Post:
        return Post(
            id=row["id"],
            course_id=row["course_id"],
            author=row["author"],
            author_id=row.get("author_id", ""),
            text=row["text"],
            posted_at=datetime.fromisoformat(row["posted_at"]) if row.get("posted_at") else None,
            posted_at_jalali=row.get("posted_at_jalali"),
            post_url=row.get("post_url"),
            is_new=bool(row.get("is_new", 1)),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
        )
