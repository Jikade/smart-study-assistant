from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_roles
from app.core.config import get_settings
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models import (
    RefreshToken,
    Role,
    User,
    UserGamification,
    UserPreference,
    UserRole,
)
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.schemas.common import MessageResponse


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

settings = get_settings()


def _issue_pair(
    db: DbSession,
    user: User,
    request: Request,
) -> TokenPair:

    roles = get_user_roles(
        db,
        user.id,
    )

    access = create_access_token(
        user.id,
        roles,
    )

    refresh, expires = create_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(
                refresh
            ),
            user_agent=request.headers.get(
                "user-agent"
            ),
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            expires_at=expires,
        )
    )

    user.last_login_at = datetime.now(
        timezone.utc
    )

    db.commit()

    db.refresh(user)

    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=(
            settings.access_token_expire_minutes
            * 60
        ),
        user=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=201,
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: DbSession,
):

    email = payload.email.lower().strip()

    existing_user = db.scalar(
        select(User)
        .where(
            User.email.ilike(email)
        )
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail=(
                "Email is already registered"
            ),
        )

    user = User(
        email=email,
        password_hash=hash_password(
            payload.password
        ),
        full_name=payload.full_name.strip(),
    )

    db.add(user)

    db.flush()

    role = db.scalar(
        select(Role)
        .where(
            Role.code == "STUDENT"
        )
    )

    if role is None:

        role = Role(
            code="STUDENT",
            name="Student",
            description=(
                "Default learner role"
            ),
        )

        db.add(role)

        db.flush()

    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.add(
        UserPreference(
            user_id=user.id,
        )
    )

    db.add(
        UserGamification(
            user_id=user.id,
        )
    )

    db.commit()

    db.refresh(user)

    return _issue_pair(
        db,
        user,
        request,
    )


@router.post(
    "/login",
    response_model=TokenPair,
)
def login(
    payload: LoginRequest,
    request: Request,
    db: DbSession,
):

    user = db.scalar(
        select(User)
        .where(
            User.email.ilike(
                payload.email.strip()
            )
        )
    )

    if user is None:

        verify_password(
            payload.password,
            DUMMY_HASH,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    if user.status != "ACTIVE":

        raise HTTPException(
            status_code=403,
            detail=(
                f"Account status is "
                f"{user.status}"
            ),
        )

    return _issue_pair(
        db,
        user,
        request,
    )


@router.post(
    "/login-form",
    response_model=TokenPair,
)
def login_form(
    form: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    request: Request,
    db: DbSession,
):

    return login(
        LoginRequest(
            email=form.username,
            password=form.password,
        ),
        request,
        db,
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
)
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: DbSession,
):

    token_hash = hash_refresh_token(
        payload.refresh_token
    )

    row = db.scalar(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash
            == token_hash
        )
    )

    now = datetime.now(
        timezone.utc
    )

    if (
        row is None
        or row.revoked_at is not None
        or row.expires_at <= now
    ):

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or expired "
                "refresh token"
            ),
        )

    user = db.get(
        User,
        row.user_id,
    )

    if (
        user is None
        or user.status != "ACTIVE"
    ):

        raise HTTPException(
            status_code=401,
            detail="User is unavailable",
        )

    row.revoked_at = now

    db.commit()

    return _issue_pair(
        db,
        user,
        request,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(
    payload: LogoutRequest,
    db: DbSession,
):

    row = db.scalar(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash
            == hash_refresh_token(
                payload.refresh_token
            )
        )
    )

    if (
        row
        and row.revoked_at is None
    ):

        row.revoked_at = datetime.now(
            timezone.utc
        )

        db.commit()

    return MessageResponse(
        message="Logged out"
    )


@router.get(
    "/me",
    response_model=UserOut,
)
def me(
    user: CurrentUser,
):
    return user