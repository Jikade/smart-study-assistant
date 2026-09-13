from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.models import Role, User, UserRole
from app.db.session import SessionLocal

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login-form")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise credentials_error
    user = db.get(User, user_id)
    if user is None or user.status != "ACTIVE":
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_user_roles(db: Session, user_id: int) -> list[str]:
    return list(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        ).all()
    )


def require_roles(*allowed: str) -> Callable:
    def dependency(db: DbSession, user: CurrentUser) -> User:
        roles = set(get_user_roles(db, user.id))
        if not roles.intersection(allowed):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
