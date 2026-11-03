"""Dependencyهای FastAPI برای احراز هویت وب."""

from __future__ import annotations

from fastapi import HTTPException, Request

from src.storage.repositories.user_repo import UserRepository
from src.web.security import SESSION_COOKIE_NAME


def get_db(request: Request):
    return request.app.state.db


def get_user_repo(request: Request) -> UserRepository:
    return UserRepository(request.app.state.db)


def get_session_manager(request: Request):
    return request.app.state.session


def get_raw_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def get_current_user(request: Request) -> dict:
    """کاربر لاگین‌شده؛ در صورت نبود session → 401."""
    token = get_raw_session_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="وارد نشده‌اید")
    repo = get_user_repo(request)
    user = repo.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="نشست منقضی یا نامعتبر است")
    return user


def get_optional_user(request: Request) -> dict | None:
    token = get_raw_session_token(request)
    if not token:
        return None
    return get_user_repo(request).get_user_by_token(token)
