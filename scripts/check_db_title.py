"""بررسی عنوان Assignment در دیتابیس."""

from src.storage.database import Database
from src.storage.repositories import AssignmentRepository


with Database("data/lms.db") as db:
    repo = AssignmentRepository(db)
    assignments = repo.get_all()

    for a in assignments:
        print(f"ID: {a.id}")
        print(f"Title: {a.title!r}")
        print(f"Length: {len(a.title)} کاراکتر")
        print()